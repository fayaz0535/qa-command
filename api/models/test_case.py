import enum
from sqlalchemy import Column, String, Text, Date, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from models.base import BaseModel
from models.defect import DefectSource


class TestStatus(str, enum.Enum):
    PASSED = "Passed"
    FAILED = "Failed"
    BLOCKED = "Blocked"
    NOT_RUN = "Not Run"
    IN_PROGRESS = "In Progress"


class TestPhase(str, enum.Enum):
    SIT = "SIT"
    UAT = "UAT"
    BVT = "BVT"
    PARALLEL_RUN = "Parallel Run"


class TestCase(BaseModel):
    __tablename__ = "test_cases"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_testcase_source_external_id"),)

    external_id = Column(String(100), nullable=False)
    source = Column(SAEnum(DefectSource, values_callable=lambda x: [e.value for e in x]), nullable=False)

    platform = Column(String(255), nullable=True)
    module = Column(String(255), nullable=True)
    sub_module = Column(String(255), nullable=True)

    title = Column(Text, nullable=False)
    status = Column(SAEnum(TestStatus, values_callable=lambda x: [e.value for e in x]),
                     default=TestStatus.NOT_RUN, nullable=False)
    phase = Column(SAEnum(TestPhase, values_callable=lambda x: [e.value for e in x]), nullable=True)
    executed_date = Column(Date, nullable=True)
