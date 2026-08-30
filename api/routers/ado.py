from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.ado_adapter import ADOAdapter
from adapters.base import SourceConfig
from config import DEFAULT_ADO_WIQL
from database import get_db
from models.ado_connection import ADOConnection
from models.defect import DefectSource
from services.crypto import encrypt_secret, decrypt_secret
from services.ingest import ingest_defects
from services.metrics import write_daily_snapshot
from services.areapath_parser import parse_area_path

router = APIRouter(prefix="/api/ado", tags=["ado"])

PAT_MASK = "••••••••"
PREVIEW_SAMPLE_SIZE = 10


async def _get_connection(db: AsyncSession) -> ADOConnection | None:
    return (await db.execute(select(ADOConnection).limit(1))).scalar_one_or_none()


async def _require_connection(db: AsyncSession) -> ADOConnection:
    connection = await _get_connection(db)
    if not connection:
        raise HTTPException(404, "No ADO connection configured yet — set one up first")
    return connection


def _serialize_connection(row: ADOConnection) -> dict:
    return {
        "connected": True,
        "org_url": row.org_url,
        "project": row.project,
        "pat_masked": PAT_MASK,
        "wiql_query": row.wiql_query or DEFAULT_ADO_WIQL,
        "last_synced_at": row.last_synced_at.isoformat() if row.last_synced_at else None,
        "last_sync_summary": row.last_sync_summary,
    }


# ── Connection setup ─────────────────────────────────────────────────────────

class TestConnectionBody(BaseModel):
    org_url: str
    project: str
    pat: str


@router.post("/test-connection")
async def test_connection(body: TestConnectionBody):
    """Verifies the PAT + org + project work — never persists anything. The PAT here
    comes straight from the request body and is discarded once this returns; it's
    never logged or echoed back."""
    adapter = ADOAdapter()
    result = await adapter.test_connection(
        SourceConfig(extra={"org_url": body.org_url, "project": body.project, "pat": body.pat})
    )
    return result


class SaveConnectionBody(BaseModel):
    org_url: str
    project: str
    pat: str
    wiql_query: str | None = None


@router.get("/connection")
async def get_connection(db: AsyncSession = Depends(get_db)):
    connection = await _get_connection(db)
    if not connection:
        return {"connected": False}
    return _serialize_connection(connection)


@router.post("/connection")
async def save_connection(body: SaveConnectionBody, db: AsyncSession = Depends(get_db)):
    """Re-tests the connection server-side before saving — never persists a PAT that
    doesn't actually authenticate. The plaintext PAT lives only in this request's
    memory; encrypt_secret() is the only thing that ever touches the database."""
    adapter = ADOAdapter()
    check = await adapter.test_connection(
        SourceConfig(extra={"org_url": body.org_url, "project": body.project, "pat": body.pat})
    )
    if not check.get("ok"):
        raise HTTPException(400, check.get("error") or "Connection test failed")

    encrypted = encrypt_secret(body.pat)
    connection = await _get_connection(db)
    if not connection:
        connection = ADOConnection(
            org_url=body.org_url, project=body.project,
            encrypted_pat=encrypted, wiql_query=body.wiql_query,
        )
        db.add(connection)
    else:
        connection.org_url = body.org_url
        connection.project = body.project
        connection.encrypted_pat = encrypted
        connection.wiql_query = body.wiql_query

    await db.commit()
    await db.refresh(connection)
    return _serialize_connection(connection)


# ── WIQL preview + sync ──────────────────────────────────────────────────────

async def _decrypted_config(connection: ADOConnection, wiql_override: str | None = None) -> SourceConfig:
    pat = decrypt_secret(connection.encrypted_pat)
    return SourceConfig(extra={
        "org_url": connection.org_url,
        "project": connection.project,
        "pat": pat,
        "wiql_query": wiql_override or connection.wiql_query or DEFAULT_ADO_WIQL,
    })


class PreviewWiqlBody(BaseModel):
    wiql_query: str


@router.post("/preview-wiql")
async def preview_wiql(body: PreviewWiqlBody, db: AsyncSession = Depends(get_db)):
    """Runs a WIQL query (not necessarily the saved one) against the already-saved
    connection and shows how many items it matches plus a sample of how their Area
    Paths parse — lets the DM sanity-check the query before saving or syncing.
    Touches nothing in the Defect table."""
    connection = await _require_connection(db)
    adapter = ADOAdapter()
    try:
        config = await _decrypted_config(connection, wiql_override=body.wiql_query)
        records = await adapter.fetch_defects(config)
    except Exception as exc:
        raise HTTPException(502, f"WIQL preview failed: {exc}")

    sample = []
    for record in records[:PREVIEW_SAMPLE_SIZE]:
        platform, module, sub_module = parse_area_path(record.raw_area_path)
        sample.append({
            "external_id": record.external_id,
            "title": record.title,
            "severity": record.severity,
            "state": record.state,
            "platform": platform,
            "module": module,
            "sub_module": sub_module,
        })

    return {"count": len(records), "sample": sample}


@router.post("/sync")
async def sync_ado(db: AsyncSession = Depends(get_db)):
    """Runs the saved WIQL, parses every returned item's Area Path, and upserts into
    Defect via the same ingest_defects() the CSV path uses — remarks-append and
    reopen-detection behave identically regardless of source."""
    connection = await _require_connection(db)
    adapter = ADOAdapter()
    try:
        config = await _decrypted_config(connection)
        records = await adapter.fetch_defects(config)
    except Exception as exc:
        raise HTTPException(502, f"ADO sync failed: {exc}")

    by_platform: dict[str, int] = {}
    for record in records:
        platform, module, sub_module = parse_area_path(record.raw_area_path)
        record.platform = platform
        record.module = module
        record.sub_module = sub_module
        by_platform[platform] = by_platform.get(platform, 0) + 1

    ingest_result = await ingest_defects(db, records, source=DefectSource.ADO)
    await write_daily_snapshot(db)

    summary = {**ingest_result, "by_platform": by_platform}
    connection.last_synced_at = datetime.utcnow()
    connection.last_sync_summary = summary
    await db.commit()

    return {"fetched": len(records), **summary}
