from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.ado_adapter import ADOAdapter
from adapters.base import SourceConfig
from config import DEFAULT_ADO_WIQL
from database import get_db
from models.ado_connection import ADOConnection
from models.areapath_mapping import AreaPathMapping, AreaPathMappingRule
from models.defect import DefectSource
from services.crypto import encrypt_secret, decrypt_secret
from services.ingest import ingest_defects
from services.metrics import write_daily_snapshot
from services.areapath_mapper import (
    apply_rule, discover_and_upsert_paths, resolve_for_ingest,
    get_or_create_rule, reapply_rule_to_unmapped,
)

router = APIRouter(prefix="/api/ado", tags=["ado"])

PAT_MASK = "••••••••"


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


# ── Sync ─────────────────────────────────────────────────────────────────────

async def _decrypted_config(connection: ADOConnection) -> SourceConfig:
    pat = decrypt_secret(connection.encrypted_pat)
    return SourceConfig(extra={
        "org_url": connection.org_url,
        "project": connection.project,
        "pat": pat,
        "wiql_query": connection.wiql_query or DEFAULT_ADO_WIQL,
    })


@router.post("/discover-paths")
async def discover_paths(db: AsyncSession = Depends(get_db)):
    """Fetches current work items just to harvest distinct Area Paths into the
    mapping table, without touching the Defect table — lets the DM set up mappings
    before ever running a real sync."""
    connection = await _require_connection(db)
    adapter = ADOAdapter()
    try:
        config = await _decrypted_config(connection)
        records = await adapter.fetch_defects(config)
    except Exception as exc:
        raise HTTPException(502, f"Could not reach ADO: {exc}")

    raw_paths = {r.raw_area_path for r in records if r.raw_area_path}
    result = await discover_and_upsert_paths(db, raw_paths)
    return {"fetched": len(records), **result}


@router.post("/sync")
async def sync_ado(db: AsyncSession = Depends(get_db)):
    """Pulls current work items, maps Area Paths, and upserts into Defect via the
    same ingest_defects() the CSV path uses — so remarks-append and reopen-detection
    behave identically regardless of source."""
    connection = await _require_connection(db)
    adapter = ADOAdapter()
    try:
        config = await _decrypted_config(connection)
        records = await adapter.fetch_defects(config)
    except Exception as exc:
        raise HTTPException(502, f"ADO sync failed: {exc}")

    raw_paths = {r.raw_area_path for r in records if r.raw_area_path}
    discovery = await discover_and_upsert_paths(db, raw_paths)

    unmapped_count = 0
    for record in records:
        if not record.raw_area_path:
            unmapped_count += 1
            continue
        mapping = await resolve_for_ingest(db, record.raw_area_path)
        record.platform = mapping.platform
        record.module = mapping.module
        record.sub_module = mapping.sub_module
        if mapping.needs_review:
            unmapped_count += 1

    ingest_result = await ingest_defects(db, records, source=DefectSource.ADO)
    await write_daily_snapshot(db)

    summary = {**ingest_result, "unmapped_count": unmapped_count, "new_area_paths": discovery["new_paths"]}
    connection.last_synced_at = datetime.utcnow()
    connection.last_sync_summary = summary
    await db.commit()

    return {"fetched": len(records), **summary}


# ── Area path mapping ────────────────────────────────────────────────────────

def _serialize_mapping(row: AreaPathMapping) -> dict:
    return {
        "id": str(row.id),
        "area_path": row.area_path,
        "platform": row.platform,
        "module": row.module,
        "sub_module": row.sub_module,
        "is_override": row.is_override,
        "needs_review": row.needs_review,
        "last_seen_at": row.last_seen_at.isoformat() if row.last_seen_at else None,
    }


@router.get("/area-paths")
async def list_area_paths(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(AreaPathMapping).order_by(AreaPathMapping.area_path))).scalars().all()
    return {
        "area_paths": [_serialize_mapping(r) for r in rows],
        "needs_review_count": sum(1 for r in rows if r.needs_review),
    }


class AreaPathOverrideBody(BaseModel):
    platform: str | None = None
    module: str | None = None
    sub_module: str | None = None


@router.put("/area-paths/{mapping_id}")
async def override_area_path(mapping_id: UUID, body: AreaPathOverrideBody, db: AsyncSession = Depends(get_db)):
    row = await db.get(AreaPathMapping, mapping_id)
    if not row:
        raise HTTPException(404, "Area path mapping not found")
    row.platform = body.platform
    row.module = body.module
    row.sub_module = body.sub_module
    row.is_override = True
    row.needs_review = not body.platform
    await db.commit()
    await db.refresh(row)
    return _serialize_mapping(row)


def _serialize_rule(rule: AreaPathMappingRule) -> dict:
    return {
        "drop_root_segments": rule.drop_root_segments,
        "platform_segments": rule.platform_segments,
        "module_segments": rule.module_segments,
    }


@router.get("/mapping-rule")
async def get_mapping_rule(db: AsyncSession = Depends(get_db)):
    rule = await get_or_create_rule(db)
    return _serialize_rule(rule)


class MappingRuleBody(BaseModel):
    drop_root_segments: int
    platform_segments: int
    module_segments: int


@router.put("/mapping-rule")
async def update_mapping_rule(body: MappingRuleBody, db: AsyncSession = Depends(get_db)):
    """Saves the rule AND immediately re-derives platform/module/sub_module for every
    non-override path — this is the 'apply' step, distinct from /area-paths/preview
    which only shows what a rule WOULD do."""
    rule = await get_or_create_rule(db)
    rule.drop_root_segments = body.drop_root_segments
    rule.platform_segments = body.platform_segments
    rule.module_segments = body.module_segments
    await db.commit()
    await db.refresh(rule)

    recomputed = await reapply_rule_to_unmapped(db, rule)
    return {**_serialize_rule(rule), "recomputed_paths": recomputed}


@router.post("/area-paths/preview")
async def preview_mapping_rule(body: MappingRuleBody, db: AsyncSession = Depends(get_db)):
    """Dry run: shows how every known, non-overridden path would map under the given
    rule, without saving the rule or touching any row."""
    hypothetical_rule = AreaPathMappingRule(
        drop_root_segments=body.drop_root_segments,
        platform_segments=body.platform_segments,
        module_segments=body.module_segments,
    )
    rows = (await db.execute(select(AreaPathMapping).order_by(AreaPathMapping.area_path))).scalars().all()

    preview = []
    for row in rows:
        if row.is_override:
            preview.append({
                "area_path": row.area_path, "platform": row.platform, "module": row.module,
                "sub_module": row.sub_module, "overridden": True, "needs_review": False,
            })
        else:
            result = apply_rule(row.area_path, hypothetical_rule)
            preview.append({
                "area_path": row.area_path, "platform": result.platform, "module": result.module,
                "sub_module": result.sub_module, "overridden": False, "needs_review": result.needs_review,
            })
    return {"preview": preview}
