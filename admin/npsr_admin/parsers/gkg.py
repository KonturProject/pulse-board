"""Воронка ГкГ НС: attempts per NS chain («Звонков на цепочку»), НС1 only, year over year.

Main path — the pivot cache inside the workbook (see pivot_cache.py): every source row with its group and
operator, so the metric goes down to employees whatever the visible pivot shows (the sheet is protected,
the workbook read-only, and the pivot itself hides СР9). The calculated field «Звонков на цепочку» is
num_dur / over_fact_traf (read from the cache formula); rows: campaign_ns_type = «1», groups of the
direction. Current year → `ns1_attempts` by employee; last year → `ns1_attempts_ly` by group, and for the
whole direction from every НП_СР group of that year (closed groups like СР4 are the YoY baseline).

Fallback for a workbook without a readable cache — the visible sheet `Звонков на цепочку длит`:
pivot rows: director → `0` (ordinary NS) / `1` (НС1, "НС-наработки", invoices from 6 min) / `Unknown`
→ branch → (groups, when the author saves the pivot expanded). Columns: `Прошлый год` / `Текущий год`
× week numbers. Values are averages, so they are kept as-is (num = value, den = 1) at the deepest level
available; only НС1 is taken.
"""

from datetime import date
from pathlib import Path

from ..excel import find_row, iter_rows, num
from ..groups import match_group
from ..model import Fact, ParseResult
from ..pivot_cache import find_cache

SHEET = "Звонков на цепочку длит"
SECTION_LABELS = {"0", "1", "Unknown", "Общий итог"}


def _label(v) -> str:
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip() if v is not None else ""


CALC_FIELD = "Звонков на цеп"


def _from_cache(path: Path, res: ParseResult) -> bool:
    """Facts from the pivot cache; False when the workbook has no such cache."""
    if Path(path).suffix.lower() != ".xlsb":
        return False
    try:
        found = find_cache(path, CALC_FIELD)
    except (ValueError, KeyError, IndexError, OSError) as e:
        res.warnings.append(f"ГкГ: кэш сводной не прочитан ({e}) — беру видимую сводную")
        return False
    if not found:
        return False
    fields, calc, rows = found
    if len(calc.refs) != 2:
        res.warnings.append("ГкГ: формула «Звонков на цепочку» изменилась — беру видимую сводную")
        return False
    num_f, den_f = fields[calc.refs[0]].name, fields[calc.refs[1]].name
    cur: dict[tuple[str, str, str], list[float]] = {}
    ly: dict[tuple[str, str], list[float]] = {}
    ly_dir: dict[int, list[float]] = {}
    years: set[int] = set()
    for r in rows:
        if str(r.get("campaign_ns_type")) != "1":
            continue
        group = match_group(r.get("group_name"))
        week = r.get("week_num_not_year")
        if not week:
            continue
        n, d = num(r.get(num_f)), num(r.get(den_f))
        last_year = r.get("y2y_period") != "Текущий год"
        if last_year and "НП_СР" in str(r.get("group_name")):
            acc = ly_dir.setdefault(int(week), [0.0, 0.0])
            acc[0] += n
            acc[1] += d
        if not group:
            continue
        if not last_year:
            years.add(int(num(r.get("Year_num"))))
            acc = cur.setdefault((int(week), group, str(r.get("operator") or "").strip()), [0.0, 0.0])
        else:
            acc = ly.setdefault((int(week), group), [0.0, 0.0])
        acc[0] += n
        acc[1] += d
    year = max(years) if years else date.fromtimestamp(Path(path).stat().st_mtime).isocalendar()[0]
    for (wk, g, op), (n, d) in cur.items():
        if d and op:
            res.facts.append(Fact("ns1_attempts", f"{year}.{wk:02d}", g, op, n, d))
    for (wk, g), (n, d) in ly.items():
        if d:
            res.facts.append(Fact("ns1_attempts_ly", f"{year}.{wk:02d}", g, None, n, d))
    for wk, (n, d) in ly_dir.items():
        if d:
            res.facts.append(Fact("ns1_attempts_ly", f"{year}.{wk:02d}", "*", None, n, d))
    return True


def parse(path: Path) -> ParseResult:
    res = ParseResult(source="gkg", data_date=None)
    if _from_cache(path, res):
        return res
    cur_year = date.fromtimestamp(Path(path).stat().st_mtime).isocalendar()[0]
    try:
        rows = iter_rows(path, SHEET)
        found = find_row(rows, "Прошлый год", "Текущий год")
    except KeyError:
        res.warnings.append(f"ГкГ: нет листа «{SHEET}»")
        return res
    if found is None:
        res.warnings.append("ГкГ: не найдена шапка «Прошлый год / Текущий год»")
        return res
    years_row = found[1]
    weeks_row = next(rows)
    label_col = next((j for j, v in enumerate(weeks_row) if isinstance(v, str) and v.strip() == "Названия строк"), 1)

    cols: dict[int, tuple[str, int]] = {}  # col -> ("cur"|"ly", week)
    year = None
    for j, v in enumerate(years_row):
        if isinstance(v, str) and v.strip() in ("Прошлый год", "Текущий год"):
            if year and "cur" in [y for y, _ in cols.values()] and v.strip() == "Прошлый год":
                break  # second measure block (YoY comparison) starts
            year = "cur" if v.strip() == "Текущий год" else "ly"
        if year and isinstance(weeks_row[j], (int, float)) and 1 <= weeks_row[j] <= 53:
            cols[j] = (year, int(weeks_row[j]))

    section = None
    ns1_row = None
    group_rows: list[tuple[str, list]] = []
    for row in rows:
        label = _label(row[label_col] if len(row) > label_col else None)
        if label in SECTION_LABELS:
            section = label
            if label == "1":
                ns1_row = row
            continue
        if section == "1" and (g := match_group(label)):
            group_rows.append((g, row))

    def emit(group: str, row: list):
        for j, (yr, wk) in cols.items():
            if j < len(row) and row[j] not in (None, ""):
                metric = "ns1_attempts" if yr == "cur" else "ns1_attempts_ly"
                res.facts.append(Fact(metric, f"{cur_year}.{wk:02d}", group, None, num(row[j]), 1))

    if group_rows:
        for g, row in group_rows:
            emit(g, row)
    elif ns1_row is not None:
        emit("*", ns1_row)
        res.warnings.append("ГкГ: сводная свёрнута до филиала — попытки НС1 только по направлению; разверните до групп")
    else:
        res.warnings.append("ГкГ: нет строки НС1 («1»)")
    return res
