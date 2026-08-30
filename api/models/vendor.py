from sqlalchemy import Column, String, UniqueConstraint
from models.base import BaseModel
from config import VENDOR_DOMAIN_MAP


class Vendor(BaseModel):
    """Known vendor names — populated from VENDOR_DOMAIN_MAP, extendable via admin later."""
    __tablename__ = "vendors"
    __table_args__ = (UniqueConstraint("domain", name="uq_vendor_domain"),)

    name = Column(String(255), nullable=False)
    domain = Column(String(255), nullable=False)


def resolve_vendor(assignee_email: str | None) -> tuple[str | None, bool]:
    """Derive owner_vendor from the assignee's email domain.

    Returns (vendor_name, needs_review). An unrecognised domain is never guessed —
    it comes back as (None, True) so the UI can flag it for manual mapping.
    """
    if not assignee_email or "@" not in assignee_email:
        return None, True

    domain = assignee_email.strip().lower().split("@")[-1]
    vendor_name = VENDOR_DOMAIN_MAP.get(domain)
    if vendor_name:
        return vendor_name, False
    return None, True
