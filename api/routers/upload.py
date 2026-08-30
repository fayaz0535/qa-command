import json
import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.base import SourceConfig
from adapters.csv_adapter import CSVAdapter, ColumnMappingRequired
from config import UPLOAD_DIR
from database import get_db
from services.ingest import ingest_defects, ingest_tests
from services.metrics import write_daily_snapshot

router = APIRouter(prefix="/api", tags=["upload"])

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    record_type: str = Form("defects"),
    column_map: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Accepts a CSV/XLSX. Auto-detects columns; if platform/module/sub_module (or
    external_id/title) can't be matched, returns a mapping_required response instead
    of ingesting — the client resubmits via /api/upload/complete-mapping."""
    if record_type not in ("defects", "tests"):
        raise HTTPException(400, "record_type must be 'defects' or 'tests'")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}' — use .csv, .xlsx or .xls")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    dest_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
    with open(dest_path, "wb") as f:
        f.write(await file.read())

    parsed_map = json.loads(column_map) if column_map else None
    adapter = CSVAdapter()
    config = SourceConfig(extra={"file_path": dest_path, "column_map": parsed_map})

    try:
        if record_type == "defects":
            records = await adapter.fetch_defects(config)
            result = await ingest_defects(db, records)
        else:
            records = await adapter.fetch_tests(config)
            result = await ingest_tests(db, records)
    except ColumnMappingRequired as exc:
        return {
            "status": "mapping_required",
            "record_type": record_type,
            "file_path": dest_path,
            "detected": exc.detected,
            "missing": exc.missing,
            "columns": exc.columns,
        }

    await write_daily_snapshot(db)
    return {"status": "ok", "record_type": record_type, **result}


class CompleteMappingRequest(BaseModel):
    file_path: str
    record_type: str
    column_map: dict[str, str]


@router.post("/upload/complete-mapping")
async def complete_mapping(body: CompleteMappingRequest, db: AsyncSession = Depends(get_db)):
    if body.record_type not in ("defects", "tests"):
        raise HTTPException(400, "record_type must be 'defects' or 'tests'")
    if not os.path.exists(body.file_path):
        raise HTTPException(404, "Uploaded file no longer available — please re-upload")

    adapter = CSVAdapter()
    config = SourceConfig(extra={
        "file_path": body.file_path,
        "column_map": body.column_map,
        "skip_mapping_check": True,
    })

    if body.record_type == "defects":
        records = await adapter.fetch_defects(config)
        result = await ingest_defects(db, records)
    else:
        records = await adapter.fetch_tests(config)
        result = await ingest_tests(db, records)

    await write_daily_snapshot(db)
    return {"status": "ok", "record_type": body.record_type, **result}
