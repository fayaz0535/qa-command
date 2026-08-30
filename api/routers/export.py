from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services import export as export_service

router = APIRouter(prefix="/api/export", tags=["export"])

MEDIA_TYPES = {
    "csv": "text/csv",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


def _scope_label(platform, module, sub_module, severity=None, owner=None, phase=None) -> str:
    parts = [p for p in [platform, module, sub_module, severity, owner, phase] if p]
    return " › ".join(parts) if parts else "All"


@router.get("/defects")
async def export_defects(
    format: str = "xlsx",
    platform: str | None = None, module: str | None = None, sub_module: str | None = None,
    severity: str | None = None, owner: str | None = None, state: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if format not in MEDIA_TYPES:
        raise HTTPException(400, "format must be one of xlsx, pdf, csv")

    defects = await export_service.get_filtered_defects(
        db, platform=platform, module=module, sub_module=sub_module,
        severity=severity, owner=owner, state=state,
    )
    scope = _scope_label(platform, module, sub_module, severity, owner)

    if format == "csv":
        content = export_service.defects_to_csv(defects)
    elif format == "xlsx":
        content = export_service.defects_to_excel(defects)
    else:
        content = export_service.defects_to_pdf(defects, scope_label=scope)

    filename = f"qa-command-defects.{format}"
    return Response(content=content, media_type=MEDIA_TYPES[format],
                     headers={"Content-Disposition": f'attachment; filename="{filename}"'})


@router.get("/tests")
async def export_tests(
    format: str = "xlsx",
    platform: str | None = None, module: str | None = None, sub_module: str | None = None,
    phase: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    if format not in MEDIA_TYPES:
        raise HTTPException(400, "format must be one of xlsx, pdf, csv")

    tests = await export_service.get_filtered_tests(
        db, platform=platform, module=module, sub_module=sub_module, phase=phase,
    )
    scope = _scope_label(platform, module, sub_module, phase=phase)

    if format == "csv":
        content = export_service.tests_to_csv(tests)
    elif format == "xlsx":
        content = export_service.tests_to_excel(tests)
    else:
        content = export_service.tests_to_pdf(tests, scope_label=scope)

    filename = f"qa-command-tests.{format}"
    return Response(content=content, media_type=MEDIA_TYPES[format],
                     headers={"Content-Disposition": f'attachment; filename="{filename}"'})
