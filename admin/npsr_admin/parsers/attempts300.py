"""Попытки в 300+ (LTV 300+), sheet of the direction by managers, left table (`300+`).

Measures `Кол-во звонков` and `Кол-во перезвонов` by week (`2026.45`); attempts = перезвоны / звонки,
which aggregates exactly as num/den. Group rows repeat under scoring categories (`Другие`,
`Категория А`) — each repetition is its own fact, so summing gives the group total.
"""

from pathlib import Path

from ..excel import find_row, iter_rows, num
from ..groups import match_group
from ..model import Fact, ParseResult

SHEET = "НП СР по менеджерам"


def _week(v) -> str | None:
    if isinstance(v, float):
        return f"{v:.2f}"
    if isinstance(v, str) and len(v) == 7 and v[4] == ".":
        return v
    return None


def parse(path: Path) -> ParseResult:
    res = ParseResult(source="attempts300", data_date=None)
    try:
        rows = iter_rows(path, SHEET)
        found = find_row(rows, "Кол-во звонков", "Кол-во перезвонов")
    except KeyError:
        res.warnings.append(f"Попытки 300+: нет листа «{SHEET}»")
        return res
    if found is None:
        res.warnings.append("Попытки 300+: не найдены «Кол-во звонков / Кол-во перезвонов»")
        return res
    measures = found[1]
    weeks = next(rows)
    label_col = next((j for j, v in enumerate(weeks) if isinstance(v, str) and v.strip() == "Названия строк"), 0)
    calls_start = measures.index("Кол-во звонков")
    recalls_start = measures.index("Кол-во перезвонов")
    calls = {_week(weeks[j]): j for j in range(calls_start, recalls_start) if _week(weeks[j])}
    recalls = {_week(weeks[j]): j for j in range(recalls_start, recalls_start + (recalls_start - calls_start)) if _week(weeks[j])}

    for row in rows:
        g = match_group(row[label_col] if len(row) > label_col else None)
        if not g:
            continue
        for wk, cj in calls.items():
            c = num(row[cj]) if cj < len(row) else 0.0
            r = num(row[recalls[wk]]) if wk in recalls and recalls[wk] < len(row) else 0.0
            if c > 0:
                res.facts.append(Fact("attempts_300", wk, g, None, r, c))
    return res
