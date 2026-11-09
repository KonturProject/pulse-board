import pytest

from npsr_admin.parsers import oz_attempts, oz_speed


def _ratio(facts, metric, week_prefix_days):
    sel = [f for f in facts if f.metric == metric and f.period in week_prefix_days]
    return sum(f.num for f in sel) / sum(f.den for f in sel), sel


def test_oz_attempts_reconcile_with_pivot(sample):
    res = oz_attempts.parse(sample("АП_НП_СР_Попытки в первичке ПИНы_ОЗ.xlsx"))
    w45 = {"2026-11-02", "2026-11-03", "2026-11-04", "2026-11-05", "2026-11-06"}
    value, sel = _ratio(res.facts, "oz_attempts", w45)
    # pivot «Попытки», week 2026.45: 140 calls, «Ср попытки любые» 6.5857
    assert sum(f.den for f in sel) == 140
    assert value == pytest.approx(6.585714285714285)
    assert {f.group for f in res.facts} <= {"СР1", "СР2", "СР3", "СР5", "СР6", "СР9"}
    assert all(f.employee for f in res.facts)


def test_oz_speed_reproduces_pivot_new(sample):
    path = sample("АП_НП_Обратный звонок_new.xlsm")
    # pivot «New», week 2026.44, «Электронный сервис»: 278 of 281 = 98.9%. Of those, our six groups
    # have 277 of 280 (the other 9 callbacks belong to other directors, none within 30 min).
    created = within = 0.0
    for r in oz_speed.pivot_rows(path):
        if r["CR_WEEK"] == "2026.44" and r["Type_Back_Call"] == "Электронный сервис" and oz_speed.match_group(r["BusinessUnit_Name"]):
            created += r["created"]
            within += r["within30"]
    assert (within, created) == (277, 280)
    assert round(within / created, 3) == round(278 / 281, 3) == 0.989


def test_oz_speed_facts_by_group_and_operator(sample):
    res = oz_speed.parse(sample("АП_НП_Обратный звонок_new.xlsm"))
    w44 = {f"2026-10-{d}" for d in range(26, 32)}
    sel = [f for f in res.facts if f.metric == "oz_speed_30" and f.period in w44]
    assert sel and 0.95 <= sum(f.num for f in sel) / sum(f.den for f in sel) <= 1
    assert res.data_date is not None
    assert {f.group for f in res.facts} <= {"СР1", "СР2", "СР3", "СР5", "СР6", "СР9"}
