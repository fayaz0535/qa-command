from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.export import get_filtered_tests

router = APIRouter(prefix="/api/tests", tags=["tests"])


def _serialize(t):
    return {
        "id": str(t.id),
        "external_id": t.external_id,
        "source": t.source.value,
        "platform": t.platform,
        "module": t.module,
        "sub_module": t.sub_module,
        "title": t.title,
        "status": t.status.value,
        "phase": t.phase.value if t.phase else None,
        "executed_date": t.executed_date.isoformat() if t.executed_date else None,
    }


@router.get("")
async def list_tests(
    platform: str | None = None, module: str | None = None, sub_module: str | None = None,
    phase: str | None = None, db: AsyncSession = Depends(get_db),
):
    tests = await get_filtered_tests(db, platform=platform, module=module, sub_module=sub_module, phase=phase)
    return {"tests": [_serialize(t) for t in tests], "count": len(tests)}
