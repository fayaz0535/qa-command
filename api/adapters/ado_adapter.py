"""Phase 2 stub — Azure DevOps adapter.

Intended implementation (fills in the same interface, nothing upstream changes):

  fetch_defects(config):
    config.extra expects: org_url, project, pat (personal access token),
    optional area_path / iteration_path filters.
    - POST {org_url}/{project}/_apis/wit/wiql?api-version=7.1
      body: {"query": "SELECT [System.Id] FROM WorkItems WHERE [System.WorkItemType] = 'Bug' ..."}
      -> returns work item ids
    - POST {org_url}/{project}/_apis/wit/workitemsbatch?api-version=7.1
      body: {"ids": [...], "fields": ["System.Id", "System.Title", "System.State",
             "Microsoft.VSTS.Common.Severity", "System.AssignedTo", "System.CreatedDate",
             "Microsoft.VSTS.Scheduling.DueDate", "System.AreaPath", "System.Tags"]}
      -> map each work item to a DefectRecord:
           external_id   = str(item["id"])
           title         = fields["System.Title"]
           severity      = map ADO severity ("1 - Critical" etc.) -> Critical/High/Medium/Low
           state         = fields["System.State"]
           platform/module/sub_module = split fields["System.AreaPath"] on "\\"
           assignee_email = fields["System.AssignedTo"]["uniqueName"]
           raised_date   = fields["System.CreatedDate"]
           eta           = fields.get("Microsoft.VSTS.Scheduling.DueDate")
    - Auth: Basic with ("", pat) — ADO accepts PAT as the password with empty username.
    - Pagination: workitemsbatch caps at 200 ids per call — chunk requests.

  fetch_tests(config):
    - Use the Test Plans API: GET {org_url}/{project}/_apis/testplan/plans?api-version=7.1
      then GET .../plans/{planId}/suites, then .../suites/{suiteId}/testcase
      and GET .../Test/Runs for executed results (outcome, state) to build TestRecord.
    - phase would come from the plan/suite name (e.g. "SIT Cycle 2") — needs a
      naming convention agreed with the ADO project admin before Phase 2.

Raises NotImplementedError until Phase 2 — kept here so the interface is stable
and Phase 2 only has to fill in the bodies below.
"""

from adapters.base import SourceAdapter, SourceConfig, DefectRecord, TestRecord


class ADOAdapter(SourceAdapter):
    def fetch_defects(self, config: SourceConfig) -> list[DefectRecord]:
        raise NotImplementedError("ADO adapter is a Phase 2 stub — see module docstring for the intended calls.")

    def fetch_tests(self, config: SourceConfig) -> list[TestRecord]:
        raise NotImplementedError("ADO adapter is a Phase 2 stub — see module docstring for the intended calls.")
