"""Deterministic metrics engine. Every number here comes from arithmetic over the
rows in Postgres — never from the LLM. services/insights.py narrates these numbers
after the fact; it never computes them.

Thresholds (RAG_THRESHOLDS, AGING_BUCKETS_DAYS, CLOSED_STATES) live in config.py so
they're easy to tune without touching this logic.
"""

from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import CLOSED_STATES, RAG_THRESHOLDS, AGING_BUCKETS_DAYS, SEVERITY_ORDER
from models.defect import Defect
from models.test_case import TestCase, TestStatus
from models.metric_snapshot import MetricSnapshot, HierarchyLevel

_HEALTH_RANK = {"green": 0, "amber": 1, "red": 2}


def _worst(healths: list[str]) -> str:
    if not healths:
        return "green"
    return max(healths, key=lambda h: _HEALTH_RANK.get(h, 0))


def _health_from_thresholds(open_by_severity: dict, execution_pct: float, aging_gt21: int,
                             high_severity_aging: bool) -> str:
    red = RAG_THRESHOLDS["red"]
    amber = RAG_THRESHOLDS["amber"]
    if open_by_severity.get("Critical", 0) >= red["min_critical_open"] \
            or aging_gt21 > 0 \
            or execution_pct < red["execution_pct_below"]:
        return "red"
    if execution_pct < amber["execution_pct_below"] or high_severity_aging:
        return "amber"
    return "green"


def node_metrics(defects: list[Defect], tests: list[TestCase]) -> dict:
    """Pure computation over an already-filtered slice of defects/tests — one hierarchy node."""
    total_tests = len(tests)
    executed = [t for t in tests if t.status != TestStatus.NOT_RUN]
    passed = [t for t in tests if t.status == TestStatus.PASSED]
    execution_pct = round(100 * len(executed) / total_tests, 1) if total_tests else 0.0
    pass_rate = round(100 * len(passed) / len(executed), 1) if executed else 0.0

    open_defects = [d for d in defects if d.state not in CLOSED_STATES]
    closed_defects = [d for d in defects if d.state in CLOSED_STATES]

    open_by_severity = {sev: 0 for sev in SEVERITY_ORDER}
    for d in open_defects:
        open_by_severity[d.severity.value] = open_by_severity.get(d.severity.value, 0) + 1

    today = date.today()
    gt7, gt14, gt21 = AGING_BUCKETS_DAYS
    aging_gt7 = aging_gt14 = aging_gt21 = 0
    high_severity_aging = False
    for d in open_defects:
        if not d.raised_date:
            continue
        age = (today - d.raised_date).days
        if age > gt7:
            aging_gt7 += 1
        if age > gt14:
            aging_gt14 += 1
            if d.severity.value == "High":
                high_severity_aging = True
        if age > gt21:
            aging_gt21 += 1

    resolved = [d for d in closed_defects if d.raised_date and d.resolved_date]
    avg_resolution_days = (
        round(sum((d.resolved_date - d.raised_date).days for d in resolved) / len(resolved), 1)
        if resolved else None
    )

    defects_by_owner: dict[str, int] = {}
    for d in open_defects:
        owner = d.owner_vendor or "Unassigned / needs review"
        defects_by_owner[owner] = defects_by_owner.get(owner, 0) + 1

    health = _health_from_thresholds(open_by_severity, execution_pct, aging_gt21, high_severity_aging)

    return {
        "execution_pct": execution_pct,
        "pass_rate": pass_rate,
        "total_tests": total_tests,
        "open_defects": len(open_defects),
        "closed_defects": len(closed_defects),
        "open_by_severity": open_by_severity,
        "aging_gt7": aging_gt7,
        "aging_gt14": aging_gt14,
        "aging_gt21": aging_gt21,
        "avg_resolution_days": avg_resolution_days,
        "defects_by_owner": defects_by_owner,
        "health": health,
    }


def build_hierarchy_tree(defects: list[Defect], tests: list[TestCase]) -> dict:
    """Groups defects/tests into Platform -> Module -> SubModule, computes each node's
    own metrics, then rolls health up as the worst of each node's children."""
    platforms: dict[str, dict] = {}

    def platform_of(x):
        return x.platform or "Unclassified"

    def module_of(x):
        return x.module

    def submodule_of(x):
        return x.sub_module

    platform_names = {platform_of(d) for d in defects} | {platform_of(t) for t in tests}

    for p_name in sorted(platform_names):
        p_defects = [d for d in defects if platform_of(d) == p_name]
        p_tests = [t for t in tests if platform_of(t) == p_name]

        module_names = {module_of(d) for d in p_defects if module_of(d)} | \
            {module_of(t) for t in p_tests if module_of(t)}

        modules: dict[str, dict] = {}
        for m_name in sorted(module_names):
            m_defects = [d for d in p_defects if module_of(d) == m_name]
            m_tests = [t for t in p_tests if module_of(t) == m_name]

            sub_names = {submodule_of(d) for d in m_defects if submodule_of(d)} | \
                {submodule_of(t) for t in m_tests if submodule_of(t)}

            sub_modules: dict[str, dict] = {}
            for s_name in sorted(sub_names):
                s_defects = [d for d in m_defects if submodule_of(d) == s_name]
                s_tests = [t for t in m_tests if submodule_of(t) == s_name]
                sub_modules[s_name] = {"name": s_name, "metrics": node_metrics(s_defects, s_tests)}

            child_healths = [sm["metrics"]["health"] for sm in sub_modules.values()]
            module_metrics = node_metrics(m_defects, m_tests)
            if child_healths:
                module_metrics["health"] = _worst(child_healths)
            modules[m_name] = {"name": m_name, "metrics": module_metrics, "sub_modules": sub_modules}

        child_healths = [m["metrics"]["health"] for m in modules.values()]
        platform_metrics = node_metrics(p_defects, p_tests)
        if child_healths:
            platform_metrics["health"] = _worst(child_healths)
        platforms[p_name] = {"name": p_name, "metrics": platform_metrics, "modules": modules}

    overall_metrics = node_metrics(defects, tests)
    platform_healths = [p["metrics"]["health"] for p in platforms.values()]
    if platform_healths:
        overall_metrics["health"] = _worst(platform_healths)

    return {"metrics": overall_metrics, "platforms": platforms}


async def compute_dashboard_metrics(session: AsyncSession, owner_vendor: str | None = None) -> dict:
    """Fetches all defects/tests and returns the full Platform > Module > Sub-module tree."""
    defect_q = select(Defect)
    if owner_vendor:
        defect_q = defect_q.where(Defect.owner_vendor == owner_vendor)
    defects = (await session.execute(defect_q)).scalars().all()
    tests = (await session.execute(select(TestCase))).scalars().all()
    return build_hierarchy_tree(list(defects), list(tests))


async def write_daily_snapshot(session: AsyncSession) -> int:
    """Persists today's metrics for overall + every platform/module/sub_module so the
    open-vs-closed trend chart has history to read. Called after every CSV ingest —
    Phase 1 has no scheduler, so 'daily' in practice means 'once per upload per day'
    (the unique constraint on (date, level, node) makes this idempotent)."""
    tree = await compute_dashboard_metrics(session)
    today = date.today()
    rows = []

    def _row(level, m, platform=None, module=None, sub_module=None):
        return dict(
            snapshot_date=today, level=level, platform=platform, module=module, sub_module=sub_module,
            execution_pct=m["execution_pct"], pass_rate=m["pass_rate"], open_defects=m["open_defects"],
            open_critical=m["open_by_severity"].get("Critical", 0),
            open_high=m["open_by_severity"].get("High", 0),
            open_medium=m["open_by_severity"].get("Medium", 0),
            open_low=m["open_by_severity"].get("Low", 0),
            closed_defects=m["closed_defects"], aging_gt7=m["aging_gt7"], aging_gt14=m["aging_gt14"],
            aging_gt21=m["aging_gt21"], avg_resolution_days=m["avg_resolution_days"], health=m["health"],
        )

    rows.append(_row(HierarchyLevel.OVERALL, tree["metrics"]))
    for p_name, p in tree["platforms"].items():
        rows.append(_row(HierarchyLevel.PLATFORM, p["metrics"], platform=p_name))
        for m_name, m in p["modules"].items():
            rows.append(_row(HierarchyLevel.MODULE, m["metrics"], platform=p_name, module=m_name))
            for s_name, s in m["sub_modules"].items():
                rows.append(_row(HierarchyLevel.SUB_MODULE, s["metrics"],
                                  platform=p_name, module=m_name, sub_module=s_name))

    for row in rows:
        existing = await session.execute(
            select(MetricSnapshot).where(
                MetricSnapshot.snapshot_date == row["snapshot_date"],
                MetricSnapshot.level == row["level"],
                MetricSnapshot.platform == row["platform"],
                MetricSnapshot.module == row["module"],
                MetricSnapshot.sub_module == row["sub_module"],
            )
        )
        record = existing.scalar_one_or_none()
        if record:
            for k, v in row.items():
                setattr(record, k, v)
        else:
            session.add(MetricSnapshot(**row))

    await session.commit()
    return len(rows)


async def get_trend(
    session: AsyncSession, level: HierarchyLevel = HierarchyLevel.OVERALL,
    platform: str | None = None, module: str | None = None, sub_module: str | None = None,
    days: int = 30,
) -> list[dict]:
    since = date.today() - timedelta(days=days)
    result = await session.execute(
        select(MetricSnapshot)
        .where(
            MetricSnapshot.level == level, MetricSnapshot.platform == platform,
            MetricSnapshot.module == module, MetricSnapshot.sub_module == sub_module,
            MetricSnapshot.snapshot_date >= since,
        )
        .order_by(MetricSnapshot.snapshot_date)
    )
    return [
        {
            "date": row.snapshot_date.isoformat(),
            "open_defects": row.open_defects,
            "closed_defects": row.closed_defects,
            "execution_pct": row.execution_pct,
            "pass_rate": row.pass_rate,
        }
        for row in result.scalars().all()
    ]
