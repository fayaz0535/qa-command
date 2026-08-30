"""Daily email — review-then-send. build_daily_email() only ever returns a draft;
nothing in Phase 1 sends anything. The Daily Report page lets the Delivery Manager
edit the key message/ask, then Download .eml or Copy HTML and send from their own
Outlook. send_via_graph() and SendConfig exist so Phase 2 can wire real auto-send
without touching this draft-building logic.
"""

import base64
from datetime import date, datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.ext.asyncio import AsyncSession

from config import WEB_URL
from services.metrics import compute_dashboard_metrics
from services.insights import get_insights
from services.export import defects_to_excel, snapshot_pdf, get_filtered_defects

HEALTH_COLOR = {"red": "#D4537E", "amber": "#EF9F27", "green": "#00C9A7"}


def _kpi_tile(label: str, value: str, sub: str = "") -> str:
    return f"""
    <td style="padding:6px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="background:#F8F9FC;border:1px solid #E5E7EB;border-radius:8px;">
        <tr><td style="padding:14px 16px;">
          <div style="font-family:Inter,Arial,sans-serif;font-size:11px;color:#6b7280;
                      text-transform:uppercase;letter-spacing:0.04em;">{label}</div>
          <div style="font-family:Inter,Arial,sans-serif;font-size:24px;font-weight:700;
                      color:#0D1117;padding-top:2px;">{value}</div>
          <div style="font-family:Inter,Arial,sans-serif;font-size:11px;color:#9ca3af;">{sub}</div>
        </td></tr>
      </table>
    </td>"""


def _health_bar_row(name: str, m: dict) -> str:
    color = HEALTH_COLOR.get(m["health"], "#9ca3af")
    pct = max(0, min(100, m["execution_pct"]))
    return f"""
    <tr>
      <td style="padding:8px 0;font-family:Inter,Arial,sans-serif;font-size:13px;color:#0D1117;width:140px;">
        {name}
      </td>
      <td style="padding:8px 0;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr><td style="background:#E5E7EB;border-radius:6px;">
            <table role="presentation" cellpadding="0" cellspacing="0" width="{pct}%">
              <tr><td style="background:{color};border-radius:6px;height:10px;font-size:1px;line-height:10px;">&nbsp;</td></tr>
            </table>
          </td></tr>
        </table>
      </td>
      <td style="padding:8px 0 8px 12px;font-family:Inter,Arial,sans-serif;font-size:12px;
                 color:#6b7280;width:70px;text-align:right;">{pct}%</td>
    </tr>"""


def render_html(tree: dict, key_message: str, ask: str, generated_at: str) -> str:
    overall = tree["metrics"]
    kpis = "".join([
        _kpi_tile("Execution", f"{overall['execution_pct']}%"),
        _kpi_tile("Pass rate", f"{overall['pass_rate']}%"),
        _kpi_tile("Open defects", str(overall["open_defects"]),
                  f"{overall['open_by_severity'].get('Critical', 0)} critical"),
        _kpi_tile("Aging &gt;21d", str(overall["aging_gt21"])),
    ])
    platform_rows = "".join(
        _health_bar_row(name, p["metrics"]) for name, p in tree.get("platforms", {}).items()
    )

    return f"""<!doctype html>
<html>
<body style="margin:0;padding:0;background:#F3F4F6;font-family:Inter,Arial,sans-serif;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F3F4F6;padding:24px 0;">
<tr><td align="center">
<table role="presentation" width="640" cellpadding="0" cellspacing="0"
       style="background:#ffffff;border-radius:12px;overflow:hidden;">
  <tr>
    <td style="background:#5B5BF6;padding:22px 28px;">
      <span style="font-family:Inter,Arial,sans-serif;font-size:20px;font-weight:700;color:#ffffff;">QA Command</span>
      <span style="font-family:Inter,Arial,sans-serif;font-size:13px;color:#E0E0FF;float:right;padding-top:4px;">
        Daily Report — {date.today().strftime('%d %b %Y')}
      </span>
    </td>
  </tr>
  <tr>
    <td style="padding:24px 28px 8px 28px;">
      <p style="font-family:Inter,Arial,sans-serif;font-size:14px;line-height:1.5;color:#0D1117;margin:0;">
        {key_message}
      </p>
    </td>
  </tr>
  <tr>
    <td style="padding:12px 20px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>{kpis}</tr></table>
    </td>
  </tr>
  <tr>
    <td style="padding:8px 28px;">
      <div style="font-family:Inter,Arial,sans-serif;font-size:13px;font-weight:700;color:#0D1117;
                  padding:12px 0 4px 0;">Platform health</div>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{platform_rows}</table>
    </td>
  </tr>
  <tr>
    <td style="padding:16px 28px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="background:#FFF3CD;border-left:4px solid #00C9A7;border-radius:6px;">
        <tr><td style="padding:14px 16px;">
          <div style="font-family:Inter,Arial,sans-serif;font-size:12px;font-weight:700;
                      color:#92400E;text-transform:uppercase;letter-spacing:0.04em;">Today's Ask</div>
          <div style="font-family:Inter,Arial,sans-serif;font-size:13px;color:#0D1117;padding-top:4px;">{ask}</div>
        </td></tr>
      </table>
    </td>
  </tr>
  <tr>
    <td style="padding:8px 28px 24px 28px;">
      <a href="{WEB_URL}" style="display:inline-block;background:#5B5BF6;color:#ffffff;
         font-family:Inter,Arial,sans-serif;font-size:13px;font-weight:600;text-decoration:none;
         padding:10px 18px;border-radius:6px;">View full dashboard</a>
    </td>
  </tr>
  <tr>
    <td style="padding:14px 28px;background:#F8F9FC;border-top:1px solid #E5E7EB;">
      <span style="font-family:Inter,Arial,sans-serif;font-size:11px;color:#9ca3af;">
        Generated {generated_at} · ZAIMAH TECHNOLOGIES · Reviewed by DM before sending
      </span>
    </td>
  </tr>
</table>
</td></tr>
</table>
</body>
</html>"""


async def build_daily_email(session: AsyncSession) -> dict:
    tree = await compute_dashboard_metrics(session)
    insight = await get_insights(tree, scope="email")
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    key_message = insight.get("progress") or "No progress summary available."
    ask = insight.get("ask") or "No immediate ask — nothing red or amber today."

    html = render_html(tree, key_message, ask, generated_at)

    defects = await get_filtered_defects(session)
    excel_bytes = defects_to_excel(defects)
    pdf_bytes = snapshot_pdf(tree)

    return {
        "subject": f"QA Command Daily Report — {date.today().isoformat()}",
        "html": html,
        "key_message": key_message,
        "risk": insight.get("risk", ""),
        "ask": ask,
        "attachments": {
            "qa-command-defects.xlsx": base64.b64encode(excel_bytes).decode("ascii"),
            "qa-command-snapshot.pdf": base64.b64encode(pdf_bytes).decode("ascii"),
        },
        "dashboard_url": WEB_URL,
        "generated_at": generated_at,
        "reviewed_by_dm": False,
    }


def build_eml(subject: str, html: str, recipients: list[str], cc: list[str],
              attachments: dict[str, str]) -> bytes:
    """Builds a standalone .eml file — the DM's edited subject/html/recipients round-trip
    through the frontend and land here unchanged; this never sends, only assembles bytes
    for the browser to download so the DM sends it from their own Outlook."""
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    if recipients:
        msg["To"] = ", ".join(recipients)
    if cc:
        msg["Cc"] = ", ".join(cc)

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(html, "html"))
    msg.attach(alt)

    for filename, b64content in (attachments or {}).items():
        content = base64.b64decode(b64content)
        part = MIMEApplication(content, Name=filename)
        part["Content-Disposition"] = f'attachment; filename="{filename}"'
        msg.attach(part)

    return msg.as_bytes()


def send_via_graph(*args, **kwargs) -> None:
    """Phase 2 stub. Intended flow once wired up:
      1. Acquire an app-only token via MSAL client-credentials grant against
         GRAPH_TENANT_ID / GRAPH_CLIENT_ID / GRAPH_CLIENT_SECRET.
      2. POST /v1.0/users/{GRAPH_SENDER_UPN}/sendMail with the draft's subject/html
         and attachments (base64 content, per SendConfig.recipients / .cc).
      3. Only ever call this after a human has flipped SendConfig.auto_send_enabled —
         Phase 1 has no code path that reaches this function.
    """
    raise NotImplementedError(
        "Auto-send is a Phase 2 feature. Phase 1 is review-then-send: use the Daily "
        "Report page's Download .eml / Copy HTML buttons to send from Outlook."
    )
