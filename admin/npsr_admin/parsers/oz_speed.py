"""Обратный звонок new: share of callbacks taken into work the same day within 30 minutes.

Reproduces the pivot `New` exactly (its filters and calculated fields were read from the workbook's
pivot cache): raw rows of sheet `Исходник` with
- NumberTypeEvent in {66661, 777771, 777772, 777773, 777774},
- new_izdgrname in the nine publishing groups the pivot keeps,
- VTM_CAN_CALL_THIS_DAY = 1;
created («Создано») = CALLS, within 30 min («Отработно ДвД за 30 мин») =
WORKED_IN_TIME_DAY_2_DAY + WORKED_IN_TIME_DAY_2_DAY_30.
Facts: the six groups of the direction (BusinessUnit_Name), by CR_DATE and operator (Operator_Name).
"""

from collections.abc import Iterator
from datetime import date
from pathlib import Path

from ..excel import excel_date, iter_rows, num
from ..groups import match_group
from ..model import Fact, ParseResult

SHEET = "Исходник"
EVENTS = {"66661", "777771", "777772", "777773", "777774"}
PUBLISHING_GROUPS = {
    "Группа Бухгалтерия", "Группа изданий Главбух", "Группа Кадры, HR и Секретариат", "Группа Право",
    "Группа Управление", "Группа Финансы", "Группа Юридических сервисов", "Система Главбух",
    "Группа Строительство и Инженерия",
}
COLUMNS = ("CR_DATE", "CR_WEEK", "ChefDir_Name", "BusinessUnit_Name", "Operator_Name", "Type_Back_Call",
           "NumberTypeEvent", "new_izdgrname", "VTM_CAN_CALL_THIS_DAY", "CALLS",
           "WORKED_IN_TIME_DAY_2_DAY", "WORKED_IN_TIME_DAY_2_DAY_30")


def _event(v) -> str:
    return str(int(v)) if isinstance(v, float) and v.is_integer() else str(v).strip()


def pivot_rows(path: Path) -> Iterator[dict]:
    """Rows that the pivot `New` counts, with `created` and `within30` added. Raises ValueError on a
    missing column."""
    rows = iter_rows(path, SHEET, max_col=120)
    header = next(rows)
    ix = {name: j for j, name in enumerate(header) if isinstance(name, str)}
    missing = [c for c in COLUMNS if c not in ix]
    if missing:
        raise ValueError(f"нет столбцов {', '.join(missing)}")
    for r in rows:
        if num(r[ix["VTM_CAN_CALL_THIS_DAY"]]) != 1 or _event(r[ix["NumberTypeEvent"]]) not in EVENTS:
            continue
        if r[ix["new_izdgrname"]] not in PUBLISHING_GROUPS:
            continue
        row = {c: r[ix[c]] for c in COLUMNS}
        row["created"] = num(row["CALLS"])
        row["within30"] = num(row["WORKED_IN_TIME_DAY_2_DAY"]) + num(row["WORKED_IN_TIME_DAY_2_DAY_30"])
        yield row


def parse(path: Path) -> ParseResult:
    res = ParseResult(source="oz_speed", data_date=None)
    acc: dict[tuple[str, str, str], list[float]] = {}
    last: date | None = None
    try:
        for r in pivot_rows(path):
            group = match_group(r["BusinessUnit_Name"])
            day = excel_date(r["CR_DATE"])
            op = r["Operator_Name"]
            if not group or not day or not op or not r["created"]:
                continue
            last = max(last or day, day)
            a = acc.setdefault((day.isoformat(), group, str(op).strip()), [0.0, 0.0])
            a[0] += r["within30"]
            a[1] += r["created"]
    except (KeyError, StopIteration):
        res.warnings.append(f"Обратный звонок: нет листа «{SHEET}»")
        return res
    except ValueError as e:
        res.warnings.append(f"Обратный звонок: {e}")
        return res
    res.facts = [Fact("oz_speed_30", d, g, o, n, c) for (d, g, o), (n, c) in acc.items()]
    res.data_date = last
    return res
