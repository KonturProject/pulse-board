from datetime import date

import openpyxl
import pytest

from npsr_admin.excel import iter_rows
from npsr_admin.groups import GROUPS, match_group
from npsr_admin.parsers import oper

SAMPLE = "Опер_отчет_2026119.xlsb"


def _direction_pct_on_date(path) -> float:
    """`% вып на дату ШТ` of the direction's own row on the `Свод` sheet (the director who owns our groups)."""
    rows = list(iter_rows(path, "Свод"))
    director = next(r[2] for r in rows if len(r) > 5 and match_group(r[5]))
    for r in rows:
        if len(r) > 9 and r[2] == director and r[3] == director and not r[4]:
            return float(r[9])
    raise AssertionError("direction row not found")


def _ratio(facts, metric, period, employee_level=False):
    sel = [f for f in facts if f.metric == metric and f.period == period and (f.employee is not None) == employee_level]
    return sum(f.num for f in sel) / sum(f.den for f in sel)


def test_oper_reconciles_with_svod(sample):
    path = sample(SAMPLE)
    res = oper.parse(path)
    assert res.data_date == date(2026, 11, 6)
    assert _ratio(res.facts, "runrate_pcs", "2026-11-06") == pytest.approx(_direction_pct_on_date(path), abs=1e-3)
    assert {f.group for f in res.facts} <= set(GROUPS)
    assert any(f.metric == "runrate_money" for f in res.facts)


def test_oper_employee_facts_exclude_fired(sample):
    res = oper.parse(sample(SAMPLE))
    emps = {f.employee for f in res.facts if f.employee}
    assert "Уволенные" not in emps and "Вакансия" not in emps
    assert len(emps) > 20


def test_oper_missing_sheet_warns(tmp_path):
    wb = openpyxl.Workbook()
    wb.active.title = "Свод"
    path = tmp_path / "Опер_отчет_x.xlsx"
    wb.save(path)
    res = oper.parse(path)
    assert any("Деньги_по дням" in w for w in res.warnings)
    assert res.facts == []
