"""Аудиоконтроль (АП_НП_СР_АК), raw rows of sheet `DATA_po_kriter` (~500k), streamed.

- ak_rg_feedback: card `АП_ОС_Практика_РГ 2.0` grades the group leader's feedback sessions — one value
  per group (employee=None), average score.
- ak_robot_coverage: unique managers of the group graded by a robot card in the week; the denominator
  (group staff that week) is filled in by the aggregator (den=0 here).
- ak_pay_term_primary / ak_pay_term_ns: criterion `3. Срок оплаты` (NS card) / `7.1. Сроки оплаты` (primary card), binary 0/100, in the robot
  cards for the primary campaign / NS — share of 100s.
"""

import re
from pathlib import Path

from ..excel import find_row, iter_rows, num
from ..groups import match_group
from ..model import Fact, ParseResult

SHEET = "DATA_po_kriter"
RG_CARD = "АП_ОС_Практика_РГ 2.0"
ROBOT_PRIMARY = "АП_МП_Оценка робота"
ROBOT_NS = "Оценка робота_НС_new"
PAY_TERM = re.compile(r"Срок\w* оплаты")  # «3. Срок оплаты» (НС) / «7.1. Сроки оплаты» (первичка)


def _week(v) -> str | None:
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return f"{v:.2f}"
    if isinstance(v, str) and len(v.strip()) == 7:
        return v.strip()
    return None


def parse(path: Path) -> ParseResult:
    res = ParseResult(source="ak", data_date=None)
    try:
        rows = iter_rows(path, SHEET, max_col=20)
        found = find_row(rows, "АК Карта качества", "М Подразделение")
    except KeyError:
        res.warnings.append(f"АК: нет листа «{SHEET}»")
        return res
    if found is None:
        res.warnings.append("АК: не найдена шапка с «АК Карта качества»")
        return res
    h = {name: j for j, name in enumerate(found[1]) if isinstance(name, str)}
    try:
        c_score, c_cnt = h["_ Оценка по критерию"], h["_ Количество оценок по критерию"]
        c_dept, c_mgr, c_week = h["М Подразделение"], h["М Менеджер"], h["t Неделя"]
        c_card, c_type, c_crit = h["АК Карта качества"], h["АК Тип критерия"], h["АК Критерий оценки"]
    except KeyError as e:
        res.warnings.append(f"АК: нет столбца {e}")
        return res

    rg: dict[tuple[str, str], list[float]] = {}
    covered: set[tuple[str, str, str]] = set()
    pay: dict[tuple[str, str, str, str], list[float]] = {}
    for row in rows:
        if len(row) <= c_type:
            continue
        card = row[c_card]
        if card not in (RG_CARD, ROBOT_PRIMARY, ROBOT_NS):
            continue
        group = match_group(row[c_dept])
        week = _week(row[c_week])
        if not group or not week:
            continue
        cnt = num(row[c_cnt]) or 1.0
        score = num(row[c_score])
        if card == RG_CARD:
            acc = rg.setdefault((week, group), [0.0, 0.0])
            acc[0] += score * cnt
            acc[1] += cnt
            continue
        mgr = str(row[c_mgr]).strip() if row[c_mgr] else None
        if mgr:
            covered.add((week, group, mgr))
        crit = row[c_crit] if c_crit < len(row) else None
        if mgr and any(isinstance(v, str) and PAY_TERM.search(v) for v in (row[c_type], crit)):
            metric = "ak_pay_term_primary" if card == ROBOT_PRIMARY else "ak_pay_term_ns"
            acc = pay.setdefault((metric, week, group, mgr), [0.0, 0.0])
            acc[0] += cnt if score >= 100 else 0.0
            acc[1] += cnt

    for (week, group), (n, d) in rg.items():
        res.facts.append(Fact("ak_rg_feedback", week, group, None, n, d))
    for week, group, mgr in covered:
        res.facts.append(Fact("ak_robot_coverage", week, group, mgr, 1, 0))
    for (metric, week, group, mgr), (n, d) in pay.items():
        res.facts.append(Fact(metric, week, group, mgr, n, d))
    return res
