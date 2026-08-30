import enum
from sqlalchemy import Column, String, Date, Float, Integer, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from models.base import BaseModel


class HierarchyLevel(str, enum.Enum):
    OVERALL = "overall"
    PLATFORM = "platform"
    MODULE = "module"
    SUB_MODULE = "sub_module"


class MetricSnapshot(BaseModel):
    """One row per (level, node, day) — read back to draw open-vs-closed trend charts."""
    __tablename__ = "metric_snapshots"
    __table_args__ = (
        UniqueConstraint("snapshot_date", "level", "platform", "module", "sub_module",
                          name="uq_snapshot_date_node"),
    )

    snapshot_date = Column(Date, nullable=False)
    level = Column(SAEnum(HierarchyLevel, values_callable=lambda x: [e.value for e in x]), nullable=False)
    platform = Column(String(255), nullable=True)
    module = Column(String(255), nullable=True)
    sub_module = Column(String(255), nullable=True)

    execution_pct = Column(Float, default=0.0, nullable=False)
    pass_rate = Column(Float, default=0.0, nullable=False)
    open_defects = Column(Integer, default=0, nullable=False)
    open_critical = Column(Integer, default=0, nullable=False)
    open_high = Column(Integer, default=0, nullable=False)
    open_medium = Column(Integer, default=0, nullable=False)
    open_low = Column(Integer, default=0, nullable=False)
    closed_defects = Column(Integer, default=0, nullable=False)
    aging_gt7 = Column(Integer, default=0, nullable=False)
    aging_gt14 = Column(Integer, default=0, nullable=False)
    aging_gt21 = Column(Integer, default=0, nullable=False)
    avg_resolution_days = Column(Float, nullable=True)
    health = Column(String(10), default="green", nullable=False)  # red | amber | green
