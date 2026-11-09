"""Дневная воронка (АП_НП_СР_Воронка_Дни_*), sheet `ВОРОНКА Первичная кампания`.

Layout: row with block names (`Взятые`, `Завершенные`, `Качественные счета`, ...), row with
sub-headers (`План`, `Факт`, `Разговоры от 20 минут, шт.`, ...), then a row of dates. Each sub-header
spans 30 columns: 5 weeks × (5 days + a `YYYY.WW` week total). Data rows carry flags in columns 0-2
(group row: col1 = 1, employee row: col2 = 1) and the name in column 6; employees follow their group.

An employee is present on a day when they have a `Взятые` plan > 0 that day; per-person facts are
emitted only for present days, so sum(num)/sum(den) gives "per person per day".
"""

from datetime import date
from pathlib import Path

from ..excel import excel_date, find_row, iter_rows, num
from ..groups import match_group
from ..model import Fact, ParseResult

SHEET = "ВОРОНКА Первичная кампания"
SPAN = 30


def _columns(blocks: list, subs: list, dates: list, block: str, sub: str) -> list[tuple[int, date]]:
    start_block = next(j for j, v in enumerate(blocks) if isinstance(v, str) and v.strip().startswith(block))
    start = next(j for j in range(start_block, len(subs)) if isinstance(subs[j], str) and subs[j].strip().startswith(sub))
    return [(j, d) for j in range(start, start + SPAN) if j < len(dates) and (d := excel_date(dates[j]))]


def parse(path: Path) -> ParseResult:
    res = ParseResult(source="funnel", data_date=None)
    try:
        rows = iter_rows(path, SHEET)
        found = find_row(rows, "Взятые", "Качественные счета")
        if found is None:
            res.warnings.append(f"Воронка: на листе «{SHEET}» не найдены блоки «Взятые» / «Качественные счета»")
            return res
        blocks = found[1]
        subs = next(rows)
        group_flag = next(j for j, v in enumerate(subs) if isinstance(v, str) and v.strip() == "группа")
        emp_flag = next(j for j, v in enumerate(subs) if isinstance(v, str) and v.strip() == "сотр")
        name_col = next(j for j, v in enumerate(blocks) if isinstance(v, str))  # the month label sits over the names
        dates = next(rows)
        cols = {
            "plan": _columns(blocks, subs, dates, "Взятые", "План"),
            "taken": _columns(blocks, subs, dates, "Взятые", "Факт"),
            "completed": _columns(blocks, subs, dates, "Завершенные", "Факт"),
            "long_presentations": _columns(blocks, subs, dates, "Разговоры от 20 минут", "Разговоры от 20 минут, шт"),
            "quality_invoices": _columns(blocks, subs, dates, "Качественные счета", "Качественные счета, шт"),
        }
    except KeyError:
        res.warnings.append(f"Воронка: нет листа «{SHEET}»")
        return res
    except StopIteration:
        res.warnings.append("Воронка: не найден один из блоков показателей")
        return res

    group = None
    last_day: date | None = None
    for row in rows:
        if len(row) <= name_col:
            continue
        if row[group_flag] == 1:
            group = match_group(row[name_col])
            continue
        if row[emp_flag] != 1 or group is None or not isinstance(row[name_col], str):
            continue
        emp = row[name_col].strip()
        values = {k: {d: num(row[j]) for j, d in c} for k, c in cols.items()}
        for d, plan in values["plan"].items():
            taken = values["taken"].get(d, 0.0)
            if taken > 0:
                last_day = max(last_day or d, d)
            if plan <= 0:
                continue
            day = d.isoformat()
            res.facts.append(Fact("staff", day, group, emp, 1, 1))
            res.facts.append(Fact("taken", day, group, emp, taken, plan))
            for metric in ("completed", "long_presentations", "quality_invoices"):
                res.facts.append(Fact(metric, day, group, emp, values[metric].get(d, 0.0), 1))

    res.data_date = last_day
    if last_day is not None:
        res.facts = [f for f in res.facts if f.period <= last_day.isoformat()]
    return res
