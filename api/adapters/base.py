"""Source Adapter Pattern — every defect/test source (CSV, ADO, Jira, ...) maps into
the same two internal record shapes below. Routers, the metrics engine, and the
insights layer only ever see DefectRecord / TestRecord, never source-specific fields.
Adding a new source in Phase 2 means writing one adapter class — nothing upstream changes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass
class DefectRecord:
    """Common internal model a defect from any source maps into before it touches the DB."""
    external_id: str
    title: str
    severity: str          # Critical | High | Medium | Low | TBC
    state: str
    platform: str | None = None
    module: str | None = None
    sub_module: str | None = None
    assignee_email: str | None = None
    raised_date: date | None = None
    eta: date | None = None
    remark: str | None = None   # a single new remark line to append, if any


@dataclass
class TestRecord:
    """Common internal model a test case from any source maps into before it touches the DB."""
    external_id: str
    title: str
    status: str             # Passed | Failed | Blocked | Not Run | In Progress
    platform: str | None = None
    module: str | None = None
    sub_module: str | None = None
    phase: str | None = None       # SIT | UAT | BVT | Parallel Run
    executed_date: date | None = None


@dataclass
class SourceConfig:
    """Per-source connection/import settings. CSV uses `extra` for the uploaded file path;
    ADO/Jira will use it for org URL, project key, PAT, board id, etc."""
    extra: dict[str, Any] = field(default_factory=dict)


class SourceAdapter(ABC):
    """Abstract base every defect/test source must implement."""

    @abstractmethod
    def fetch_defects(self, config: SourceConfig) -> list[DefectRecord]:
        ...

    @abstractmethod
    def fetch_tests(self, config: SourceConfig) -> list[TestRecord]:
        ...
