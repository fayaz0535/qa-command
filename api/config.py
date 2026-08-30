import os

CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/uploads")

WEB_URL = os.environ.get("WEB_URL", "http://localhost:3004")

# ── Metrics thresholds (config-driven so they're easy to tune) ─────────────────
AGING_BUCKETS_DAYS = [7, 14, 21]

RAG_THRESHOLDS = {
    "red": {
        "min_critical_open": 1,
        "aging_days_breach": 21,
        "execution_pct_below": 50,
    },
    "amber": {
        "execution_pct_below": 75,
        "high_severity_aging_days_breach": 14,
    },
}

CLOSED_STATES = {"Closed", "Deferred", "Rejected"}

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low", "TBC"]

VENDOR_DOMAIN_MAP = {
    "eibank.com": "EIBank",
    "xilligence.com": "EIBank",
    "accenture.com": "Accenture",
    "accenture.cn": "Accenture",
    "maveric-systems.com": "Maveric",
}

# ── ADO (Phase 2) ────────────────────────────────────────────────────────────
ADO_ENCRYPTION_KEY = os.environ.get("ADO_ENCRYPTION_KEY", "")

DEFAULT_ADO_WIQL = (
    "SELECT [System.Id] FROM WorkItems "
    "WHERE [System.WorkItemType] = 'Bug' AND [System.State] <> 'Closed' "
    "ORDER BY [System.CreatedDate] DESC"
)

# Area Path parsing is WIQL-driven, not a config screen: the DM's query decides
# WHICH work items come in, and every returned item's System.AreaPath is split
# on "\" the same deterministic way every time. EIB's paths look like
# "EIB\Core\LOS\MultiCollateral" — (root)\Platform\Module\Sub-module.

# How many leading segments are the root project node(s) to drop before
# Platform/Module/Sub-module begin (e.g. "EIB" -> 1). Bump this if the root
# nesting turns out deeper once we see real ADO data.
ADO_AREA_PATH_DROP_SEGMENTS = 1

# A path deeper than Platform\Module\Sub-module (i.e. more than 3 segments
# after the drop) has to fold its extra segments somewhere. True joins all of
# them into Sub-module with " / " (e.g. "MultiCollateral / Deep"); False keeps
# only the first of the extra segments and drops anything deeper. Flip this
# one constant once real path depth is observed — nothing else needs to change.
ADO_AREA_PATH_JOIN_EXTRA_SUBMODULE_SEGMENTS = True
