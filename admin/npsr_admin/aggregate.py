"""Facts → the dashboard payload (schemaVersion 1), for a 4-week window ending at yesterday's week.

Value at any level = sum(num) / sum(den). Group level comes from group-level facts (employee=None)
when a source provides them, else from the sum of its employees; direction comes from `*` facts when
present, else from the groups. Period keys: day `YYYY-MM-DD`, week `YYYY.WW`, week-to-date
`YYYY.WW~YYYY-MM-DD` (for the absolute norm check).
"""

from collections import defaultdict
from datetime import date, datetime, timedelta

from .groups import BRANCHES, GROUPS
from .model import Fact
from .store import SourceInfo
from .weeks import iso_week, last_working_day

WINDOW_WEEKS = 4
CUMULATIVE = {"runrate_money", "runrate_pcs"}  # month-to-date by construction: week value = last day
NEEDS_STAFF = {"ak_robot_coverage", "orders_extra_seats", "orders_schools", "orders_periodicals"}
COUNT_EMPLOYEES = {"ak_robot_coverage"}  # numerator = number of distinct employees
HIDDEN = {"staff"}


def _sum(facts) -> tuple[float, float]:
    return sum(f.num for f in facts), sum(f.den for f in facts)


def _levels(facts: list[Fact]) -> dict[str, tuple[float, float]]:
    """(num, den) per entity key for one metric and one period bucket."""
    out: dict[str, tuple[float, float]] = {}
    by_group: dict[str, list[Fact]] = defaultdict(list)
    star = [f for f in facts if f.group == "*"]
    for f in facts:
        if f.group != "*":
            by_group[f.group].append(f)
    for g, fs in by_group.items():
        emps: dict[str, list[Fact]] = defaultdict(list)
        for f in fs:
            if f.employee is not None:
                emps[f.employee].append(f)
        for e, efs in emps.items():
            out[f"e:{g}:{e}"] = _sum(efs)
        own = [f for f in fs if f.employee is None]
        out[f"g:{g}"] = _sum(own) if own else _sum(fs)
    for b in BRANCHES:
        parts = [out[f"g:{g}"] for g in by_group if GROUPS[g].branch == b]
        if parts:
            out[f"br:{b}"] = (sum(p[0] for p in parts), sum(p[1] for p in parts))
    if star:
        out["dir"] = _sum(star)
    elif by_group:
        parts = [out[f"g:{g}"] for g in by_group]
        out["dir"] = (sum(p[0] for p in parts), sum(p[1] for p in parts))
    return out


def _values(levels: dict[str, tuple[float, float]]) -> dict[str, float]:
    return {k: round(n / d, 4) for k, (n, d) in levels.items() if d}


def _staff_levels(staff: list[Fact]) -> dict[str, float]:
    """Distinct present employees per group / branch / direction."""
    people = defaultdict(set)
    for f in staff:
        people[f.group].add(f.employee)
    out = {f"g:{g}": len(p) for g, p in people.items()}
    for b in BRANCHES:
        n = sum(len(p) for g, p in people.items() if GROUPS[g].branch == b)
        if n:
            out[f"br:{b}"] = n
    if people:
        out["dir"] = sum(len(p) for p in people.values())
    return out


def _back_working_days(d: date, n: int) -> date:
    while n > 0:
        d -= timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def build_payload(facts: list[Fact], sources: list[SourceInfo], norms: dict, today: date,
                  duck_threshold: float = 0.15, allowed_lag: dict[str, int] | None = None) -> dict:
    end_day = last_working_day(today)
    end_monday = end_day - timedelta(days=end_day.weekday())
    weeks = [iso_week(end_monday - timedelta(weeks=i)) for i in reversed(range(WINDOW_WEEKS))]
    first_day = (end_monday - timedelta(weeks=WINDOW_WEEKS - 1)).isoformat()
    last = end_day.isoformat()

    daily = [f for f in facts if "-" in f.period and first_day <= f.period <= last]
    weekly = [f for f in facts if "-" not in f.period and f.period in weeks]
    days = {w: sorted({f.period for f in daily if iso_week(date.fromisoformat(f.period)) == w}) for w in weeks}

    by_metric_day: dict[str, dict[str, list[Fact]]] = defaultdict(lambda: defaultdict(list))
    for f in daily:
        by_metric_day[f.metric][f.period].append(f)
    by_metric_week: dict[str, dict[str, list[Fact]]] = defaultdict(lambda: defaultdict(list))
    for f in weekly:
        by_metric_week[f.metric][f.period].append(f)

    staff_week = {w: _staff_levels([f for d in days[w] for f in by_metric_day["staff"].get(d, [])]) for w in weeks}

    values: dict[str, dict[str, dict[str, float]]] = {}
    for metric, per_day in by_metric_day.items():
        if metric in HIDDEN:
            continue
        mv: dict[str, dict[str, float]] = {}
        for w in weeks:
            wdays = [d for d in days[w] if d in per_day]
            for i, d in enumerate(wdays):
                mv[d] = _values(_levels(per_day[d]))
                if metric in CUMULATIVE:
                    mv[f"{w}~{d}"] = mv[d]
                else:
                    mv[f"{w}~{d}"] = _values(_levels([f for x in wdays[: i + 1] for f in per_day[x]]))
            if wdays:
                mv[w] = mv[wdays[-1]] if metric in CUMULATIVE else _values(_levels([f for x in wdays for f in per_day[x]]))
        values[metric] = mv
    for metric, per_week in by_metric_week.items():
        mv = values.setdefault(metric, {})
        for w, fs in per_week.items():
            if metric in NEEDS_STAFF:
                if metric in COUNT_EMPLOYEES:
                    people = defaultdict(set)
                    for f in fs:
                        people[f.group].add(f.employee)
                    nums = {g: len(e) for g, e in people.items()}
                else:
                    nums = {k[2:]: n for k, (n, _) in _levels(fs).items() if k.startswith("g:")}
                staff = staff_week[w]
                cap = 1.0 if metric in COUNT_EMPLOYEES else float("inf")  # a share of staff cannot exceed 100%
                present = [g for g in nums if staff.get(f"g:{g}")]  # only groups the report has, on both sides
                out = {f"g:{g}": nums[g] / staff[f"g:{g}"] for g in present}
                for b in BRANCHES:
                    gs = [g for g in present if GROUPS[g].branch == b]
                    if gs:
                        out[f"br:{b}"] = sum(nums[g] for g in gs) / sum(staff[f"g:{g}"] for g in gs)
                if present:
                    out["dir"] = sum(nums[g] for g in present) / sum(staff[f"g:{g}"] for g in present)
                mv[w] = {k: round(min(cap, v), 4) for k, v in out.items()}
            else:
                mv[w] = _values(_levels(fs))

    entities: dict[str, dict] = {"dir": {"label": "Направление"}}
    for b in BRANCHES:
        entities[f"br:{b}"] = {"label": b}
    for g in GROUPS.values():
        entities[f"g:{g.key}"] = {"label": g.label, "branch": g.branch}
    for mv in values.values():
        for per in mv.values():
            for k in per:
                if k.startswith("e:") and k not in entities:
                    _, g, name = k.split(":", 2)
                    entities[k] = {"label": name, "group": g}

    lag = allowed_lag or {}
    src = []
    for s in sources:
        stale = bool(s.data_date) and s.data_date < _back_working_days(end_day, lag.get(s.source, 1) - 1)
        src.append({"id": s.source, "dataDate": s.data_date.isoformat() if s.data_date else None,
                    "collectedAt": s.collected_at, "stale": stale})
    dated = [s.data_date for s in sources if s.data_date]

    return {
        "schemaVersion": 1,
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "dataDate": max(dated).isoformat() if dated else None,
        "weeks": weeks,
        "days": days,
        "sources": src,
        "norms": norms,
        "duckThreshold": duck_threshold,
        "entities": entities,
        "values": values,
    }
