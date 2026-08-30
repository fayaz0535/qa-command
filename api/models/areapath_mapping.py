from sqlalchemy import Column, String, Boolean, Integer, DateTime, UniqueConstraint
from models.base import BaseModel


class AreaPathMapping(BaseModel):
    """One row per distinct ADO Area Path seen. platform/module/sub_module are either
    a DM-confirmed override (is_override=True) or the last computed result of applying
    AreaPathMappingRule (is_override=False) — recomputed whenever the rule changes."""
    __tablename__ = "area_path_mappings"
    __table_args__ = (UniqueConstraint("area_path", name="uq_area_path"),)

    area_path = Column(String(1000), nullable=False)
    platform = Column(String(255), nullable=True)
    module = Column(String(255), nullable=True)
    sub_module = Column(String(255), nullable=True)
    is_override = Column(Boolean, default=False, nullable=False)
    needs_review = Column(Boolean, default=True, nullable=False)
    last_seen_at = Column(DateTime, nullable=True)


class AreaPathMappingRule(BaseModel):
    """Singleton row — the default splitting rule applied to any Area Path without an
    explicit per-path override. E.g. "EIB\\FCCM\\Alerts\\Sanctions" with
    drop_root_segments=1, platform_segments=1, module_segments=1 -> platform="FCCM",
    module="Alerts", sub_module="Sanctions" (remaining segments joined by " / ")."""
    __tablename__ = "area_path_mapping_rules"

    drop_root_segments = Column(Integer, default=1, nullable=False)
    platform_segments = Column(Integer, default=1, nullable=False)
    module_segments = Column(Integer, default=1, nullable=False)
