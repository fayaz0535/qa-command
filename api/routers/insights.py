from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.metrics import compute_dashboard_metrics
from services.insights import get_insights

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("")
async def get_dashboard_insights(force: bool = False, db: AsyncSession = Depends(get_db)):
    """Progress / Risk / Ask, narrated by Claude over today's already-computed metrics.
    Cached per calendar day — pass force=true to regenerate."""
    tree = await compute_dashboard_metrics(db)
    return await get_insights(tree, scope="overall", force=force)
