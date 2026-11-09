"""Попытки в первичке ПИНы_ОЗ, raw rows of sheet `Источник`.

Reproduces the `Попытки` pivot (the source is pre-filtered on the direction): campaign status `Обратный звонок/Онлайн-заявка`,
`Нужно ли делать >1 попытки` = `Нужно`; attempts = average `Кол_во_перезвонов` per PIN, i.e.
num = Кол_во_перезвонов, den = 1 per row. By day, group, manager.
"""

from datetime import date
from pathlib import Path

from ..excel import excel_date, iter_rows, num
from ..groups import match_group
from ..model import Fact, ParseResult

SHEET = "Источник"
CAMPAIGN = "Обратный звонок/Онлайн-заявка"
NEED = "Нужно"
COLUMNS = ("Руководитель_направления", "Подразделение", "Менеджер", "Дата", "Кол_во_перезвонов",
           "Camp_status", "Нужно ли делать >1 попытки")


def parse(path: Path) -> ParseResult:
    res = ParseResult(source="oz_attempts", data_date=None)
    try:
        rows = iter_rows(path, SHEET)
        header = next(rows)
    except (KeyError, StopIteration):
        res.warnings.append(f"Попытки ОЗ: нет листа «{SHEET}»")
        return res
    ix = {name: j for j, name in enumerate(header) if isinstance(name, str)}
    missing = [c for c in COLUMNS if c not in ix]
    if missing:
        res.warnings.append(f"Попытки ОЗ: нет столбцов {', '.join(missing)}")
        return res
    acc: dict[tuple[str, str, str], list[float]] = {}
    last: date | None = None
    for r in rows:
        if r[ix["Camp_status"]] != CAMPAIGN or r[ix["Нужно ли делать >1 попытки"]] != NEED:
            continue
        group = match_group(r[ix["Подразделение"]])
        day = excel_date(r[ix["Дата"]])
        mgr = r[ix["Менеджер"]]
        if not group or not day or not mgr:
            continue
        last = max(last or day, day)
        a = acc.setdefault((day.isoformat(), group, str(mgr).strip()), [0.0, 0.0])
        a[0] += num(r[ix["Кол_во_перезвонов"]])
        a[1] += 1
    res.facts = [Fact("oz_attempts", d, g, m, n, c) for (d, g, m), (n, c) in acc.items()]
    res.data_date = last
    return res
