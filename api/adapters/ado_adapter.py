"""Phase 2 — Azure DevOps adapter.

Auth: HTTP Basic with an empty username and the PAT as the password. The PAT
itself never comes from anywhere but the caller's SourceConfig.extra — this
module never reads, stores, or logs it; the encrypted-at-rest handling lives
in services/crypto.py and the connection is decrypted just-in-time by
routers/ado.py for the duration of one sync.

fetch_tests() is intentionally still a stub: ADO doesn't expose test
execution results through the work-item WIQL/batch APIs used here — that
needs the separate Test Plans API (plans -> suites -> test cases -> runs),
which requires a naming convention for phase (SIT/UAT/...) agreed with the
ADO project admin before it can map cleanly to TestRecord. Out of scope for
this pass, which is defects-only per the Phase 2 spec.
"""

from datetime import datetime, date

import httpx

from adapters.base import SourceAdapter, SourceConfig, DefectRecord, TestRecord

API_VERSION = "7.1"
BATCH_SIZE = 200  # ADO's max ids per workitemsbatch call
REQUEST_TIMEOUT = 30.0

DEFECT_FIELDS = [
    "System.Id",
    "System.Title",
    "System.State",
    "Microsoft.VSTS.Common.Severity",
    "System.AssignedTo",
    "System.CreatedDate",
    "System.AreaPath",
    "Microsoft.VSTS.Scheduling.DueDate",
]

# ADO severities are free text like "1 - Critical" / "2 - High" — match on the
# leading token (number or word) rather than the whole string.
SEVERITY_MAP = {
    "1": "Critical", "critical": "Critical",
    "2": "High", "high": "High",
    "3": "Medium", "medium": "Medium",
    "4": "Low", "low": "Low",
}


def _normalize_severity(raw: str | None) -> str:
    if not raw:
        return "TBC"
    token = raw.split("-")[0].strip().lower()
    return SEVERITY_MAP.get(token, "TBC")


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _auth(pat: str) -> tuple[str, str]:
    return ("", pat)


def _extract_assignee_email(fields: dict) -> str | None:
    assigned_to = fields.get("System.AssignedTo")
    if isinstance(assigned_to, dict):
        return assigned_to.get("uniqueName") or assigned_to.get("email")
    if isinstance(assigned_to, str) and "<" in assigned_to and ">" in assigned_to:
        # legacy "Display Name <email>" string format from older API versions
        return assigned_to.split("<", 1)[1].split(">", 1)[0].strip()
    return None


class ADOAdapter(SourceAdapter):
    """SourceConfig.extra expects: org_url, project, pat, and optionally wiql_query
    (falls back to config.DEFAULT_ADO_WIQL if not given)."""

    async def test_connection(self, config: SourceConfig) -> dict:
        """Lightweight auth + project-existence check, used by the settings screen's
        'Test connection' button before anything is saved."""
        org_url = config.extra["org_url"].rstrip("/")
        project = config.extra["project"]
        pat = config.extra["pat"]
        url = f"{org_url}/_apis/projects/{project}?api-version={API_VERSION}"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, auth=_auth(pat))
        except httpx.HTTPError as exc:
            return {"ok": False, "error": f"Could not reach {org_url}: {exc}"}

        if resp.status_code == 200:
            data = resp.json()
            return {"ok": True, "project_name": data.get("name"), "project_id": data.get("id")}
        if resp.status_code == 401:
            return {"ok": False, "error": "Authentication failed — check the Personal Access Token"}
        if resp.status_code == 404:
            return {"ok": False, "error": f"Project '{project}' not found at that organization URL"}
        return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

    async def _run_wiql(self, client: httpx.AsyncClient, org_url: str, project: str,
                         pat: str, wiql: str) -> list[int]:
        url = f"{org_url}/{project}/_apis/wit/wiql?api-version={API_VERSION}"
        resp = await client.post(url, auth=_auth(pat), json={"query": wiql})
        resp.raise_for_status()
        return [item["id"] for item in resp.json().get("workItems", [])]

    async def _fetch_batch(self, client: httpx.AsyncClient, org_url: str, pat: str,
                            ids: list[int], fields: list[str]) -> list[dict]:
        url = f"{org_url}/_apis/wit/workitemsbatch?api-version={API_VERSION}"
        resp = await client.post(url, auth=_auth(pat), json={"ids": ids, "fields": fields})
        resp.raise_for_status()
        return resp.json().get("value", [])

    async def _fetch_work_items(self, config: SourceConfig, fields: list[str]) -> list[dict]:
        from config import DEFAULT_ADO_WIQL  # local import avoids a config->adapters cycle

        org_url = config.extra["org_url"].rstrip("/")
        project = config.extra["project"]
        pat = config.extra["pat"]
        wiql = config.extra.get("wiql_query") or DEFAULT_ADO_WIQL

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            ids = await self._run_wiql(client, org_url, project, pat, wiql)
            items: list[dict] = []
            for i in range(0, len(ids), BATCH_SIZE):
                chunk = ids[i:i + BATCH_SIZE]
                items.extend(await self._fetch_batch(client, org_url, pat, chunk, fields))
        return items

    async def fetch_defects(self, config: SourceConfig) -> list[DefectRecord]:
        items = await self._fetch_work_items(config, DEFECT_FIELDS)
        records: list[DefectRecord] = []
        for item in items:
            fields = item.get("fields", {})
            records.append(DefectRecord(
                external_id=str(item.get("id") or fields.get("System.Id")),
                title=fields.get("System.Title") or "Untitled",
                severity=_normalize_severity(fields.get("Microsoft.VSTS.Common.Severity")),
                state=fields.get("System.State") or "Unknown",
                assignee_email=_extract_assignee_email(fields),
                raised_date=_parse_date(fields.get("System.CreatedDate")),
                eta=_parse_date(fields.get("Microsoft.VSTS.Scheduling.DueDate")),
                raw_area_path=fields.get("System.AreaPath"),
            ))
        return records

    async def fetch_tests(self, config: SourceConfig) -> list[TestRecord]:
        raise NotImplementedError(
            "ADO test-result sync needs the Test Plans API (plans -> suites -> runs), "
            "not the work-item WIQL/batch APIs used for defects — out of scope for this "
            "pass. See the module docstring."
        )
