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
