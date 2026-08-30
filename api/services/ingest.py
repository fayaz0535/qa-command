"""Turns adapter output (DefectRecord/TestRecord — source-agnostic) into database rows.

Remarks preservation: Defect is uniquely keyed by (source, external_id), so that
row *is* the PRESERVED_REMARKS store — re-uploading a CSV looks up the existing row
by external_id and only ever appends to `remarks`, never overwrites it. A reopen
(external_id was Closed/Deferred/Rejected, reappears not-closed) is detected the
same way, and the prior remark history is already sitting on that row.
"""

from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.base import DefectRecord, TestRecord
from config import CLOSED_STATES
from models.defect import Defect, DefectSource, DefectSeverity
from models.test_case import TestCase, TestStatus, TestPhase
from models.hierarchy import get_or_create_hierarchy
from models.vendor import resolve_vendor


def _remark_line(text: str) -> str:
    return f"{date.today().isoformat()}: {text} [sync]"


async def ingest_defects(
    session: AsyncSession, records: list[DefectRecord], source: DefectSource = DefectSource.CSV
) -> dict:
    created, updated, reopened = 0, 0, 0

    for rec in records:
        result = await session.execute(
            select(Defect).where(Defect.source == source, Defect.external_id == rec.external_id)
        )
        existing = result.scalar_one_or_none()

        vendor_name, needs_review = resolve_vendor(rec.assignee_email)
        await get_or_create_hierarchy(session, rec.platform, rec.module, rec.sub_module)

        try:
            severity = DefectSeverity(rec.severity)
        except ValueError:
            severity = DefectSeverity.TBC

        if existing is None:
            defect = Defect(
                external_id=rec.external_id,
                source=source,
                platform=rec.platform,
                module=rec.module,
                sub_module=rec.sub_module,
                title=rec.title,
                severity=severity,
                state=rec.state,
                owner_vendor=vendor_name,
                vendor_needs_review=needs_review,
                assignee_email=rec.assignee_email,
                raised_date=rec.raised_date,
                eta=rec.eta,
                resolved_date=date.today() if rec.state in CLOSED_STATES else None,
                remarks=_remark_line("Uploaded"),
                is_reopen=False,
            )
            session.add(defect)
            created += 1
            continue

        changes = []
        was_closed = existing.state in CLOSED_STATES
        is_now_closed = rec.state in CLOSED_STATES

        if existing.state != rec.state:
            changes.append(f"State {existing.state} -> {rec.state}")
        if existing.severity != severity:
            changes.append(f"Severity {existing.severity.value} -> {severity.value}")
        if existing.eta != rec.eta:
            changes.append(f"ETA {existing.eta} -> {rec.eta}")
        if existing.assignee_email != rec.assignee_email:
            changes.append(f"Reassigned to {rec.assignee_email or 'unassigned'}")

        is_reopen = was_closed and not is_now_closed
        if is_reopen:
            changes.append(f"Reopened (was {existing.state})")
            existing.is_reopen = True
            existing.resolved_date = None
            reopened += 1
        elif not was_closed and is_now_closed:
            existing.resolved_date = date.today()

        if changes:
            existing.remarks = (existing.remarks or "") + "\n" + _remark_line("; ".join(changes))
            updated += 1

        existing.title = rec.title
        existing.severity = severity
        existing.state = rec.state
        existing.platform = rec.platform
        existing.module = rec.module
        existing.sub_module = rec.sub_module
        existing.owner_vendor = vendor_name
        existing.vendor_needs_review = needs_review
        existing.assignee_email = rec.assignee_email
        existing.raised_date = rec.raised_date
        existing.eta = rec.eta

    await session.commit()
    return {"created": created, "updated": updated, "reopened": reopened, "total": len(records)}


async def ingest_tests(
    session: AsyncSession, records: list[TestRecord], source: DefectSource = DefectSource.CSV
) -> dict:
    created, updated = 0, 0

    for rec in records:
        result = await session.execute(
            select(TestCase).where(TestCase.source == source, TestCase.external_id == rec.external_id)
        )
        existing = result.scalar_one_or_none()
        await get_or_create_hierarchy(session, rec.platform, rec.module, rec.sub_module)

        status = TestStatus(rec.status) if rec.status in [s.value for s in TestStatus] else TestStatus.NOT_RUN
        phase = TestPhase(rec.phase) if rec.phase in [p.value for p in TestPhase] else None

        if existing is None:
            session.add(TestCase(
                external_id=rec.external_id,
                source=source,
                platform=rec.platform,
                module=rec.module,
                sub_module=rec.sub_module,
                title=rec.title,
                status=status,
                phase=phase,
                executed_date=rec.executed_date,
            ))
            created += 1
        else:
            existing.title = rec.title
            existing.status = status
            existing.phase = phase
            existing.platform = rec.platform
            existing.module = rec.module
            existing.sub_module = rec.sub_module
            existing.executed_date = rec.executed_date
            updated += 1

    await session.commit()
    return {"created": created, "updated": updated, "total": len(records)}
