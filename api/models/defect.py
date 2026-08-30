import enum
from datetime import date
from sqlalchemy import Column, String, Text, Date, Boolean, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from models.base import BaseModel


class DefectSource(str, enum.Enum):
    CSV = "CSV"
    ADO = "ADO"
    JIRA = "JIRA"


class DefectSeverity(str, enum.Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    TBC = "TBC"


class Defect(BaseModel):
    __tablename__ = "defects"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_defect_source_external_id"),)

    external_id = Column(String(100), nullable=False)
    source = Column(SAEnum(DefectSource, values_callable=lambda x: [e.value for e in x]), nullable=False)

    platform = Column(String(255), nullable=True)
    module = Column(String(255), nullable=True)
    sub_module = Column(String(255), nullable=True)

    title = Column(Text, nullable=False)
    severity = Column(SAEnum(DefectSeverity, values_callable=lambda x: [e.value for e in x]),
                       default=DefectSeverity.TBC, nullable=False)
    state = Column(String(100), nullable=False)

    owner_vendor = Column(String(255), nullable=True)
    vendor_needs_review = Column(Boolean, default=False, nullable=False)
    assignee_email = Column(String(255), nullable=True)

    raised_date = Column(Date, nullable=True)
    eta = Column(Date, nullable=True)
    resolved_date = Column(Date, nullable=True)  # set when state first transitions into CLOSED_STATES

    remarks = Column(Text, default="", nullable=False)  # append-only, never overwritten on re-upload
    is_reopen = Column(Boolean, default=False, nullable=False)

    @property
    def aging_days(self) -> int | None:
        """Computed, not persisted — always reflects 'as of today'."""
        if not self.raised_date:
            return None
        return (date.today() - self.raised_date).days
