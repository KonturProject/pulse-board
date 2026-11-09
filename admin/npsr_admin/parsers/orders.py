"""Свод по заказам: invoices for extra seats, schools and periodicals (the direction's sheets).

Each sheet is a pivot: rows = groups (no employees), columns = week numbers (`40`..`45`), and inside each
week three measures — `клиентов`, the count (`Допмест` / ` ШТ_Школы` / ` ШТ_Периодика`) and a share.
Counts become group-level facts (employee=None) with den=0: the aggregator divides by the group's staff
of that week, giving "per employee" as the author asked.
"""

from datetime import date
from pathlib import Path

from ..excel import iter_rows, num
from ..groups import match_group
from ..model import Fact, ParseResult

SHEETS = {
    "orders_extra_seats": ("НП СР допместа", "Допмест"),
    "orders_schools": ("НП СР РС Школы", "ШТ_Школы"),
    "orders_periodicals": ("НП СР РС Периодика", "ШТ_Периодика"),
}


def _week_no(v) -> int | None:
    if isinstance(v, (int, float)) and not isinstance(v, bool) and 1 <= v <= 53:
        return int(v)
    if isinstance(v, str) and v.strip().isdigit():
        return int(v.strip())
    return None


def _parse_sheet(path: Path, sheet: str, count_label: str, year: int, metric: str, res: ParseResult):
    prev: list = []
    cols: dict[int, str] = {}
    label_col = 1
    for row in iter_rows(path, sheet, max_col=40):
        if not cols:
            if any(isinstance(v, str) and v.strip() == "Названия строк" for v in row) and any(
                isinstance(v, str) and v.strip() == count_label for v in row
            ):
                label_col = next(j for j, v in enumerate(row) if isinstance(v, str) and v.strip() == "Названия строк")
                for j, v in enumerate(row):
                    if isinstance(v, str) and v.strip() == count_label and j > 0 and (wk := _week_no(prev[j - 1] if j - 1 < len(prev) else None)):
                        cols[j] = f"{year}.{wk:02d}"
            prev = row
            continue
        label = row[label_col] if len(row) > label_col else None
        if isinstance(label, str) and label.strip() == "Общий итог":
            break
        g = match_group(label)
        if g:
            for j, week in cols.items():
                res.facts.append(Fact(metric, week, g, None, num(row[j]) if j < len(row) else 0.0, 0))
    if not cols:
        res.warnings.append(f"Свод по заказам: на листе «{sheet}» не найдены столбцы «{count_label}» по неделям")


def parse(path: Path) -> ParseResult:
    res = ParseResult(source="orders", data_date=None)
    year = date.fromtimestamp(Path(path).stat().st_mtime).isocalendar()[0]
    for metric, (sheet, label) in SHEETS.items():
        try:
            _parse_sheet(path, sheet, label, year, metric, res)
        except KeyError:
            res.warnings.append(f"Свод по заказам: нет листа «{sheet}»")
    return res
