"""Phase 1's only live source. Reads a CSV/XLSX upload, auto-detects columns (headers
vary sheet to sheet), and maps rows into the common DefectRecord / TestRecord shapes.

Column auto-detection only goes as far as reading raw source values — normalisation
(severity vocabulary, state casing, vendor lookup), de-duplication against existing
rows, and remarks preservation all happen downstream in services/ingest.py, which is
the piece that actually knows about the database.
"""

import os
import pandas as pd
from datetime import date

from adapters.base import SourceAdapter, SourceConfig, DefectRecord, TestRecord


class ColumnMappingRequired(Exception):
    """Raised when platform/module/sub_module (or another required field) couldn't be
    auto-detected and no explicit column_map override was supplied in SourceConfig.extra.
    The upload router catches this and returns a column-mapping step to the client."""

    def __init__(self, detected: dict, missing: list[str], columns: list[str]):
        self.detected = detected
        self.missing = missing
        self.columns = columns
        super().__init__(f"Column mapping required — missing: {missing}")


# field -> lowercased header aliases we try to auto-match against, in priority order
DEFECT_COLUMN_ALIASES: dict[str, list[str]] = {
    "external_id":     ["id", "bug id", "defect id", "issue id", "key", "work item id"],
    "title":           ["title", "summary", "defect title", "bug title"],
    "assignee_email":  ["assigned to email", "assignee email", "assigned to", "assignee", "owner"],
    "state":           ["state", "status"],
    "severity":        ["severity", "priority"],
    "raised_date":     ["raised date", "created date", "opened date", "raised on", "reported date"],
    "eta":             ["eta", "due date", "target date", "target resolution date"],
    "platform":        ["platform"],
    "module":          ["module"],
    "sub_module":      ["sub-module", "sub module", "submodule"],
    "tags":            ["tags", "labels"],
}

TEST_COLUMN_ALIASES: dict[str, list[str]] = {
    "external_id":     ["id", "test case id", "tc id", "test id", "key"],
    "title":           ["title", "test case", "test case title", "summary"],
    "status":          ["status", "result", "test status", "execution status"],
    "phase":           ["phase", "test phase", "cycle", "test cycle"],
    "executed_date":   ["executed date", "execution date", "run date", "date executed"],
    "platform":        ["platform"],
    "module":          ["module"],
    "sub_module":      ["sub-module", "sub module", "submodule"],
}

# Required for the hierarchy drill-down (Executive/Delivery views group by these) —
# if none of these auto-detect, force a column-mapping step rather than guess.
HIERARCHY_FIELDS = ["platform", "module", "sub_module"]

SEVERITY_ALIASES = {
    "critical": "Critical", "1": "Critical", "p1": "Critical", "sev1": "Critical", "s1": "Critical",
    "high": "High", "2": "High", "p2": "High", "sev2": "High", "s2": "High",
    "medium": "Medium", "3": "Medium", "p3": "Medium", "sev3": "Medium", "s3": "Medium", "med": "Medium",
    "low": "Low", "4": "Low", "p4": "Low", "sev4": "Low", "s4": "Low",
}

TEST_STATUS_ALIASES = {
    "pass": "Passed", "passed": "Passed",
    "fail": "Failed", "failed": "Failed",
    "block": "Blocked", "blocked": "Blocked",
    "not run": "Not Run", "not executed": "Not Run", "notrun": "Not Run", "pending": "Not Run",
    "in progress": "In Progress", "in-progress": "In Progress", "running": "In Progress",
}

TEST_PHASE_ALIASES = {
    "sit": "SIT", "system integration testing": "SIT",
    "uat": "UAT", "user acceptance testing": "UAT",
    "bvt": "BVT", "build verification test": "BVT",
    "parallel run": "Parallel Run", "parallel-run": "Parallel Run",
}


def _read_table(file_path: str) -> pd.DataFrame:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, dtype=str)
    else:
        df = pd.read_csv(file_path, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    return df.where(pd.notnull(df), None)


def _detect_columns(columns: list[str], aliases: dict[str, list[str]]) -> dict[str, str | None]:
    lower_map = {c.lower().strip(): c for c in columns}
    detected: dict[str, str | None] = {}
    for field, candidates in aliases.items():
        match = None
        for candidate in candidates:
            if candidate in lower_map:
                match = lower_map[candidate]
                break
        detected[field] = match
    return detected


def _parse_date(value) -> date | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.date()
    except Exception:
        return None


_VALID_SEVERITIES = {"critical", "high", "medium", "low", "tbc"}


def _normalize_severity(raw: str | None) -> str:
    if not raw:
        return "TBC"
    cleaned = str(raw).strip().lower()
    if cleaned in _VALID_SEVERITIES:
        return cleaned.title()
    return SEVERITY_ALIASES.get(cleaned, "TBC")


def _normalize_test_status(raw: str | None) -> str:
    if not raw:
        return "Not Run"
    return TEST_STATUS_ALIASES.get(str(raw).strip().lower(), "Not Run")


def _normalize_phase(raw: str | None) -> str | None:
    if not raw:
        return None
    return TEST_PHASE_ALIASES.get(str(raw).strip().lower())


class CSVAdapter(SourceAdapter):
    """SourceConfig.extra expects:
        file_path:   str  — path to the uploaded CSV/XLSX (required)
        column_map:  dict[str, str] — explicit field->header override from the
                     column-mapping step (optional; skips auto-detection for those fields)
    """

    def detect_defect_columns(self, file_path: str) -> dict:
        df = _read_table(file_path)
        detected = _detect_columns(list(df.columns), DEFECT_COLUMN_ALIASES)
        missing_hierarchy = [f for f in HIERARCHY_FIELDS if not detected.get(f)]
        return {"detected": detected, "missing_hierarchy": missing_hierarchy, "columns": list(df.columns)}

    async def fetch_defects(self, config: SourceConfig) -> list[DefectRecord]:
        file_path = config.extra["file_path"]
        override = config.extra.get("column_map") or {}
        df = _read_table(file_path)

        detected = _detect_columns(list(df.columns), DEFECT_COLUMN_ALIASES)
        detected.update({k: v for k, v in override.items() if v})

        missing_hierarchy = [f for f in HIERARCHY_FIELDS if not detected.get(f)]
        if missing_hierarchy and not config.extra.get("skip_mapping_check"):
            raise ColumnMappingRequired(detected, missing_hierarchy, list(df.columns))

        if not detected.get("external_id") or not detected.get("title"):
            raise ColumnMappingRequired(detected, ["external_id", "title"], list(df.columns))

        records: list[DefectRecord] = []
        for _, row in df.iterrows():
            def get(field):
                col = detected.get(field)
                return row[col] if col and col in row else None

            external_id = get("external_id")
            title = get("title")
            if not external_id or not title:
                continue

            records.append(DefectRecord(
                external_id=str(external_id).strip(),
                title=str(title).strip(),
                severity=_normalize_severity(get("severity")),
                state=str(get("state") or "Open").strip(),
                platform=(str(get("platform")).strip() if get("platform") else None),
                module=(str(get("module")).strip() if get("module") else None),
                sub_module=(str(get("sub_module")).strip() if get("sub_module") else None),
                assignee_email=(str(get("assignee_email")).strip() if get("assignee_email") else None),
                raised_date=_parse_date(get("raised_date")),
                eta=_parse_date(get("eta")),
            ))
        return records

    async def fetch_tests(self, config: SourceConfig) -> list[TestRecord]:
        file_path = config.extra["file_path"]
        override = config.extra.get("column_map") or {}
        df = _read_table(file_path)

        detected = _detect_columns(list(df.columns), TEST_COLUMN_ALIASES)
        detected.update({k: v for k, v in override.items() if v})

        if not detected.get("external_id") or not detected.get("title"):
            raise ColumnMappingRequired(detected, ["external_id", "title"], list(df.columns))

        records: list[TestRecord] = []
        for _, row in df.iterrows():
            def get(field):
                col = detected.get(field)
                return row[col] if col and col in row else None

            external_id = get("external_id")
            title = get("title")
            if not external_id or not title:
                continue

            records.append(TestRecord(
                external_id=str(external_id).strip(),
                title=str(title).strip(),
                status=_normalize_test_status(get("status")),
                platform=(str(get("platform")).strip() if get("platform") else None),
                module=(str(get("module")).strip() if get("module") else None),
                sub_module=(str(get("sub_module")).strip() if get("sub_module") else None),
                phase=_normalize_phase(get("phase")),
                executed_date=_parse_date(get("executed_date")),
            ))
        return records
