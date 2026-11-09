"""Воронка ГкГ НС, sheet `Звонков на цепочку длит`: attempts per NS chain, year over year.

Pivot rows: director → `0` (ordinary NS) / `1` (НС1, "НС-наработки", invoices from 6 min) / `Unknown`
→ branch → (groups, when the author saves the pivot expanded). Columns: `Прошлый год` / `Текущий год`
× week numbers. Values are averages, so they are kept as-is (num = value, den = 1) at the deepest level
available; only НС1 is taken.
"""

from datetime import date
from pathlib import Path

from ..excel import find_row, iter_rows, num
from ..groups import match_group
from ..model import Fact, ParseResult

SHEET = "Звонков на цепочку длит"
SECTION_LABELS = {"0", "1", "Unknown", "Общий итог"}


def _label(v) -> str:
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip() if v is not None else ""


def parse(path: Path) -> ParseResult:
    res = ParseResult(source="gkg", data_date=None)
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
