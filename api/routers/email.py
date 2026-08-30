from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.send_config import SendConfig
from services.email_builder import build_daily_email, build_eml

router = APIRouter(prefix="/api/email", tags=["email"])


@router.post("/draft")
async def draft_email(db: AsyncSession = Depends(get_db)):
    """Builds today's email — returns a draft only, never sends. The DM edits the
    key message / ask in the Daily Report page before doing anything with it."""
    return await build_daily_email(db)


class EmlRequest(BaseModel):
    subject: str
    html: str
    recipients: list[str] = []
    cc: list[str] = []
    attachments: dict[str, str] = {}


@router.post("/eml")
async def download_eml(body: EmlRequest):
    """Assembles the (possibly DM-edited) draft into a .eml file for the browser to
    download. Never sends — the DM opens it in Outlook and sends it themselves."""
    eml_bytes = build_eml(body.subject, body.html, body.recipients, body.cc, body.attachments)
    return Response(
        content=eml_bytes,
        media_type="message/rfc822",
        headers={"Content-Disposition": 'attachment; filename="qa-command-daily-report.eml"'},
    )


class SendConfigBody(BaseModel):
    recipients: list[str] = []
    cc: list[str] = []
    send_time: str = "08:00"


@router.get("/send-config")
async def get_send_config(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SendConfig).limit(1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        cfg = SendConfig()
        db.add(cfg)
        await db.commit()
        await db.refresh(cfg)
    return {
        "recipients": cfg.recipients, "cc": cfg.cc,
        "send_time": cfg.send_time, "auto_send_enabled": cfg.auto_send_enabled,
    }


@router.put("/send-config")
async def update_send_config(body: SendConfigBody, db: AsyncSession = Depends(get_db)):
    """auto_send_enabled is intentionally not settable here — it stays False until
    Phase 2 wires up send_via_graph()."""
    result = await db.execute(select(SendConfig).limit(1))
    cfg = result.scalar_one_or_none()
    if not cfg:
        cfg = SendConfig()
        db.add(cfg)
    cfg.recipients = body.recipients
    cfg.cc = body.cc
    cfg.send_time = body.send_time
    await db.commit()
    await db.refresh(cfg)
    return {
        "recipients": cfg.recipients, "cc": cfg.cc,
        "send_time": cfg.send_time, "auto_send_enabled": cfg.auto_send_enabled,
    }
