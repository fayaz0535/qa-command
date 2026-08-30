"""AI insight layer — Claude narrates numbers the metrics engine already computed.
It never does arithmetic and never sees raw defect/test rows, only the metrics dict
from services/metrics.py. Cached per calendar day per scope so the dashboard doesn't
re-call Claude on every page load.
"""

import asyncio
import json
from datetime import date

import anthropic

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

# In-memory, per-process cache keyed by "YYYY-MM-DD:scope" — good enough for Phase 1's
# single-instance deployment; a restart just regenerates the day's insight once.
_cache: dict[str, dict] = {}

_SYSTEM_PROMPT = (
    "You are the delivery status voice for QA Command, a test-execution and defect "
    "dashboard. You are given ONLY pre-computed metrics — never raw rows — and must "
    "never invent or recalculate numbers. Write like a delivery manager's concise "
    "status note: three short lines, one sentence each, no preamble, no markdown."
)


def _summarize_for_prompt(tree: dict) -> dict:
    overall = tree["metrics"]
    platforms = []
    for name, p in tree.get("platforms", {}).items():
        m = p["metrics"]
        platforms.append({
            "platform": name,
            "health": m["health"],
            "execution_pct": m["execution_pct"],
            "open_defects": m["open_defects"],
            "open_critical": m["open_by_severity"].get("Critical", 0),
            "aging_gt21": m["aging_gt21"],
            "top_owners": sorted(m["defects_by_owner"].items(), key=lambda kv: -kv[1])[:3],
        })
    return {
        "overall": {
            "health": overall["health"],
            "execution_pct": overall["execution_pct"],
            "pass_rate": overall["pass_rate"],
            "open_defects": overall["open_defects"],
            "open_by_severity": overall["open_by_severity"],
            "aging_gt7": overall["aging_gt7"],
            "aging_gt14": overall["aging_gt14"],
            "aging_gt21": overall["aging_gt21"],
            "avg_resolution_days": overall["avg_resolution_days"],
        },
        "platforms": platforms,
    }


def _build_prompt(tree: dict) -> str:
    summary = _summarize_for_prompt(tree)
    return (
        "Here are today's computed QA metrics (JSON):\n\n"
        f"{json.dumps(summary, indent=2)}\n\n"
        "Return exactly 3 lines, each starting with its label:\n"
        "Progress: <one sentence on execution/pass-rate momentum>\n"
        "Risk: <one sentence naming the single biggest risk, with the specific number>\n"
        "Ask: <one sentence naming the blocking platform/module, its owner vendor, "
        "and the concrete action needed>\n"
        "Use only the numbers given. If nothing is red/amber, say so plainly in Risk "
        "and make Ask a light-touch follow-up instead of inventing a blocker."
    )


def _parse_response(text: str) -> dict:
    lines = {"progress": "", "risk": "", "ask": ""}
    for line in text.strip().splitlines():
        line = line.strip()
        lower = line.lower()
        if lower.startswith("progress:"):
            lines["progress"] = line.split(":", 1)[1].strip()
        elif lower.startswith("risk:"):
            lines["risk"] = line.split(":", 1)[1].strip()
        elif lower.startswith("ask:"):
            lines["ask"] = line.split(":", 1)[1].strip()
    return lines


def _cache_key(scope: str) -> str:
    return f"{date.today().isoformat()}:{scope}"


async def get_insights(tree: dict, scope: str = "overall", force: bool = False) -> dict:
    key = _cache_key(scope)
    if not force and key in _cache:
        return _cache[key]

    if not ANTHROPIC_API_KEY:
        result = {
            "progress": "AI insights are not configured — set ANTHROPIC_API_KEY.",
            "risk": "", "ask": "", "generated": False, "generated_at": date.today().isoformat(),
        }
        _cache[key] = result
        return result

    prompt = _build_prompt(tree)

    def _call():
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=400,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    try:
        text = await asyncio.to_thread(_call)
        parsed = _parse_response(text)
    except Exception as exc:
        parsed = {"progress": "Insight generation failed.", "risk": str(exc), "ask": ""}

    parsed["generated"] = True
    parsed["generated_at"] = date.today().isoformat()
    _cache[key] = parsed
    return parsed
