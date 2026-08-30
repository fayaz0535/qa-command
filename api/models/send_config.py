from sqlalchemy import Column, String, Boolean, JSON
from models.base import BaseModel


class SendConfig(BaseModel):
    """Recipients + send settings for the daily email. Phase 1: review-then-send only —
    `auto_send_enabled` exists for Phase 2 and must stay False until Graph is wired up."""
    __tablename__ = "send_configs"

    name = Column(String(255), default="Daily QA Report", nullable=False)
    recipients = Column(JSON, default=list, nullable=False)   # list[str] emails
    cc = Column(JSON, default=list, nullable=False)           # list[str] emails
    send_time = Column(String(5), default="08:00", nullable=False)  # "HH:MM", 24h
    auto_send_enabled = Column(Boolean, default=False, nullable=False)
