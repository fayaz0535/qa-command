from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.metric_snapshot import HierarchyLevel
from services.metrics import compute_dashboard_metrics, get_trend

router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("")
async def get_metrics(owner: str | None = None, db: AsyncSession = Depends(get_db)):
    """Full Platform > Module > Sub-module tree with metrics + RAG health at every node.
    `owner` filters to one vendor's defects — used by the Owner view (test totals are
    left unfiltered since tests aren't owned by a vendor)."""
    return await compute_dashboard_metrics(db, owner_vendor=owner)


@router.get("/trend")
async def get_metrics_trend(
    level: HierarchyLevel = HierarchyLevel.OVERALL,
    platform: str | None = None, module: str | None = None, sub_module: str | None = None,
    days: int = 30, db: AsyncSession = Depends(get_db),
):
    """Open-vs-closed trend line, read from daily metric_snapshot history."""
    return {"trend": await get_trend(db, level=level, platform=platform, module=module,
                                      sub_module=sub_module, days=days)}
