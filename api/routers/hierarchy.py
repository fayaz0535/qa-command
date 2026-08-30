from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.hierarchy import Platform, Module, SubModule
from models.defect import Defect
from models.vendor import resolve_vendor  # noqa: F401 — re-exported for other routers' convenience

router = APIRouter(prefix="/api", tags=["hierarchy"])


@router.get("/hierarchy")
async def get_hierarchy(db: AsyncSession = Depends(get_db)):
    """Platform > Module > Sub-module tree, for the filter bar's cascading dropdowns."""
    platforms = (await db.execute(select(Platform).order_by(Platform.name))).scalars().all()
    tree = []
    for p in platforms:
        modules = (await db.execute(
            select(Module).where(Module.platform_id == p.id).order_by(Module.name)
        )).scalars().all()
        module_list = []
        for m in modules:
            subs = (await db.execute(
                select(SubModule).where(SubModule.module_id == m.id).order_by(SubModule.name)
            )).scalars().all()
            module_list.append({"name": m.name, "sub_modules": [s.name for s in subs]})
        tree.append({"name": p.name, "modules": module_list})
    return {"platforms": tree}


@router.get("/owners")
async def list_owners(db: AsyncSession = Depends(get_db)):
    """Distinct owner vendors (for the Owner view selector) + a count of defects
    flagged for vendor-mapping review."""
    result = await db.execute(select(Defect.owner_vendor).distinct())
    owners = sorted([row[0] for row in result.all() if row[0]])

    review_count_result = await db.execute(
        select(Defect.id).where(Defect.vendor_needs_review == True)  # noqa: E712
    )
    needs_review = len(review_count_result.all())

    return {"owners": owners, "needs_review_count": needs_review}
