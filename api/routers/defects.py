from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.export import get_filtered_defects

router = APIRouter(prefix="/api/defects", tags=["defects"])


def _serialize(d):
    return {
        "id": str(d.id),
        "external_id": d.external_id,
        "source": d.source.value,
        "platform": d.platform,
        "module": d.module,
        "sub_module": d.sub_module,
        "title": d.title,
        "severity": d.severity.value,
        "state": d.state,
        "owner_vendor": d.owner_vendor,
        "vendor_needs_review": d.vendor_needs_review,
        "assignee_email": d.assignee_email,
        "raised_date": d.raised_date.isoformat() if d.raised_date else None,
        "eta": d.eta.isoformat() if d.eta else None,
        "aging_days": d.aging_days,
        "resolved_date": d.resolved_date.isoformat() if d.resolved_date else None,
        "is_reopen": d.is_reopen,
        "remarks": d.remarks,
    }


@router.get("")
async def list_defects(
    platform: str | None = None, module: str | None = None, sub_module: str | None = None,
    severity: str | None = None, owner: str | None = None, state: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    defects = await get_filtered_defects(
        db, platform=platform, module=module, sub_module=sub_module,
        severity=severity, owner=owner, state=state,
    )
    return {"defects": [_serialize(d) for d in defects], "count": len(defects)}
