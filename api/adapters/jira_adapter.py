"""Phase 2 stub — Jira adapter.

Intended implementation (fills in the same interface, nothing upstream changes):

  fetch_defects(config):
    config.extra expects: base_url, email, api_token, project_key,
    optional jql_filter (e.g. restrict to a fixVersion / sprint).
    - Auth: HTTP Basic with (email, api_token) — base64-encoded in the Authorization header.
    - GET {base_url}/rest/api/3/search
        params: jql=f'project = "{project_key}" AND issuetype = Bug',
                fields="summary,status,priority,assignee,created,duedate,
                        customfield_XXXXX (Platform/Module/Sub-module, if modelled
                        as custom fields rather than components), labels"
        -> paginate via startAt/maxResults until total is exhausted
      map each issue to a DefectRecord:
           external_id   = issue["key"]
           title         = fields["summary"]
           severity      = map fields["priority"]["name"] -> Critical/High/Medium/Low
           state         = fields["status"]["name"]
           platform/module/sub_module = from components[] or custom fields
             (needs a mapping agreed with the Jira project admin — components are
             free text and vary per project)
           assignee_email = fields["assignee"]["emailAddress"]
           raised_date   = fields["created"]
           eta           = fields.get("duedate")

  fetch_tests(config):
    - If Xray/Zephyr is installed, use its REST API for test execution results
      (Jira's own issue search doesn't model test runs/status/phase natively).
    - Without a test-management plugin, Phase 2 would need a documented convention
      (e.g. a "Test" issue type with a custom "Execution Status" field) before this
      can return a real list[TestRecord].

Raises NotImplementedError until Phase 2 — kept here so the interface is stable
and Phase 2 only has to fill in the bodies below.
"""

from adapters.base import SourceAdapter, SourceConfig, DefectRecord, TestRecord


class JiraAdapter(SourceAdapter):
    async def fetch_defects(self, config: SourceConfig) -> list[DefectRecord]:
        raise NotImplementedError("Jira adapter is a Phase 2 stub — see module docstring for the intended calls.")

    async def fetch_tests(self, config: SourceConfig) -> list[TestRecord]:
        raise NotImplementedError("Jira adapter is a Phase 2 stub — see module docstring for the intended calls.")
