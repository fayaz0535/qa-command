"""Turns an ADO Area Path string into (platform, module, sub_module) — deterministic,
config-driven, never a guess. A path that doesn't have enough segments to fill at
least platform+module is flagged needs_review rather than silently assigned.

Two ways a path's mapping is decided:
  1. A DM-confirmed override in AreaPathMapping (is_override=True) — always wins,
     never recomputed by a rule change, never flagged for review.
  2. AreaPathMappingRule applied mechanically — recomputed for every non-override
     row whenever the rule is saved (see routers/ado.py's update_mapping_rule).
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.areapath_mapping import AreaPathMapping, AreaPathMappingRule


@dataclass
class MappingResult:
    platform: str | None
    module: str | None
    sub_module: str | None
    needs_review: bool


def split_area_path(area_path: str) -> list[str]:
    return [seg.strip() for seg in area_path.split("\\") if seg.strip()]


def apply_rule(area_path: str, rule: AreaPathMappingRule) -> MappingResult:
    segments = split_area_path(area_path)
    remaining = segments[rule.drop_root_segments:] if rule.drop_root_segments < len(segments) else []

    if not remaining:
        return MappingResult(None, None, None, needs_review=True)

    platform_segs = remaining[:rule.platform_segments]
    rest = remaining[rule.platform_segments:]
    module_segs = rest[:rule.module_segments]
    sub_segs = rest[rule.module_segments:]

    platform = " / ".join(platform_segs) or None
    module = " / ".join(module_segs) or None
    sub_module = " / ".join(sub_segs) or None

    return MappingResult(platform, module, sub_module, needs_review=platform is None or module is None)


async def get_or_create_rule(session: AsyncSession) -> AreaPathMappingRule:
    result = await session.execute(select(AreaPathMappingRule).limit(1))
    rule = result.scalar_one_or_none()
    if not rule:
        rule = AreaPathMappingRule()
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
    return rule


async def discover_and_upsert_paths(session: AsyncSession, raw_paths: set[str]) -> dict:
    """Ensures every distinct path has an AreaPathMapping row, computing a default
    mapping for any brand-new one. Never touches an existing row's platform/module/
    sub_module (that's the rule-update or per-path-override's job)."""
    rule = await get_or_create_rule(session)
    now = datetime.utcnow()
    new_count = 0

    for path in raw_paths:
        existing = (await session.execute(
            select(AreaPathMapping).where(AreaPathMapping.area_path == path)
        )).scalar_one_or_none()

        if existing:
            existing.last_seen_at = now
            continue

        result = apply_rule(path, rule)
        session.add(AreaPathMapping(
            area_path=path, platform=result.platform, module=result.module,
            sub_module=result.sub_module, is_override=False,
            needs_review=result.needs_review, last_seen_at=now,
        ))
        new_count += 1

    await session.commit()
    return {"new_paths": new_count, "total_paths": len(raw_paths)}


async def resolve_for_ingest(session: AsyncSession, area_path: str) -> MappingResult:
    """Looks up the already-discovered mapping for one path at sync/ingest time.
    Assumes discover_and_upsert_paths already ran for this sync batch."""
    row = (await session.execute(
        select(AreaPathMapping).where(AreaPathMapping.area_path == area_path)
    )).scalar_one_or_none()
    if not row:
        # Shouldn't happen if discovery ran first, but never silently guess.
        return MappingResult(None, None, None, needs_review=True)
    return MappingResult(row.platform, row.module, row.sub_module, row.needs_review)


async def reapply_rule_to_unmapped(session: AsyncSession, rule: AreaPathMappingRule) -> int:
    """Recomputes platform/module/sub_module for every non-override row using the
    (already-updated) rule. Overridden rows are left exactly as the DM set them."""
    rows = (await session.execute(
        select(AreaPathMapping).where(AreaPathMapping.is_override == False)  # noqa: E712
    )).scalars().all()

    for row in rows:
        result = apply_rule(row.area_path, rule)
        row.platform = result.platform
        row.module = result.module
        row.sub_module = result.sub_module
        row.needs_review = result.needs_review

    await session.commit()
    return len(rows)
