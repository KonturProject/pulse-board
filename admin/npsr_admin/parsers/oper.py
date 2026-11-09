"""Опер_отчет: month run-rate (% of plan to date), money and pieces.

Sheets `Деньги_по дням` / `Штуки_по дням`: rows Директор → Филиал → Группа → Сотрудник, each with
`План` / `Факт` / `Отклон.` lines and one column per day of the month (header row with `Месяц`,
`Накоп-но`, then Excel date serials). Group subtotal rows (no employee) become group-level facts;
employee rows become employee facts (`Уволенные` is a bucket, not a person — dropped at employee level).

For each day d up to the data date: num = fact summed from the 1st to d, den = plan summed likewise.
"""

from collections import defaultdict
from datetime import date
from pathlib import Path

from ..excel import excel_date, find_row, iter_rows, num
from ..groups import match_group
from ..model import Fact, ParseResult

SHEETS = {"runrate_money": "Деньги_по дням", "runrate_pcs": "Штуки_по дням"}
KINDS = {"План", "Факт", "Отклон."}
NOT_PEOPLE = {"Уволенные", "Вакансия"}


def _read_sheet(path: Path, sheet: str):
    rows = iter_rows(path, sheet)
    head = find_row(rows, "Месяц", "Накоп-но")
    if head is None:
        raise ValueError(f"{sheet}: не найдена строка с датами (Месяц / Накоп-но)")
    date_cols = [(j, d) for j, v in enumerate(head[1]) if (d := excel_date(v))]
    lines: dict[tuple[str, str | None], dict[str, list[float]]] = defaultdict(dict)
    for row in rows:
        kind = next((v for v in row[:12] if isinstance(v, str) and v in KINDS), None)
        if kind not in ("План", "Факт"):
            continue
        gcol = next((j for j, v in enumerate(row[:12]) if match_group(v)), None)
        if gcol is None:
            continue
        group = match_group(row[gcol])
        emp = row[gcol + 1] if isinstance(row[gcol + 1], str) and row[gcol + 1] not in KINDS else None
        if emp in NOT_PEOPLE:
            continue
        lines[(group, emp)][kind] = [num(row[j]) if j < len(row) else 0.0 for j, _ in date_cols]
    return [d for _, d in date_cols], lines


def parse(path: Path) -> ParseResult:
    res = ParseResult(source="oper", data_date=None)
    sheets = {}
    for metric, sheet in SHEETS.items():
        try:
            sheets[metric] = _read_sheet(path, sheet)
        except KeyError:
            res.warnings.append(f"Опер_отчет: нет листа «{sheet}»")
        except ValueError as e:
            res.warnings.append(f"Опер_отчет: {e}")
    if not sheets:
        return res

    data_date: date | None = None
    for dates, lines in sheets.values():
        fact_by_day = [0.0] * len(dates)
        for (group, emp), kinds in lines.items():
            if emp is None:
                for i, v in enumerate(kinds.get("Факт", [])):
                    fact_by_day[i] += v
        days_with_fact = [d for d, v in zip(dates, fact_by_day) if v > 0]
        if days_with_fact:
            data_date = max(data_date or days_with_fact[-1], max(days_with_fact))
    res.data_date = data_date
    if data_date is None:
        res.warnings.append("Опер_отчет: нет ни одного дня с фактом")
        return res

    for metric, (dates, lines) in sheets.items():
        for (group, emp), kinds in lines.items():
            plan, fact = kinds.get("План"), kinds.get("Факт")
            if plan is None or fact is None:
                continue
            cum_p = cum_f = 0.0
            for d, p, f in zip(dates, plan, fact):
                if d > data_date:
                    break
                cum_p += p
                cum_f += f
                if cum_p > 0:
                    res.facts.append(Fact(metric, d.isoformat(), group, emp, cum_f, cum_p))
    return res
