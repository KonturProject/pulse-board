from datetime import date

import pytest

from npsr_admin.excel import find_row, iter_rows, num
from npsr_admin.groups import match_group
from npsr_admin.parsers import funnel_days

SAMPLE = "АП_НП_СР_Воронка_Дни*.xlsx"
SHEET = "ВОРОНКА Первичная кампания"


@pytest.fixture(scope="module")
def parsed(request):
    from tests.conftest import SAMPLES_DIR

    found = sorted(SAMPLES_DIR.glob(SAMPLE))
    if not found:
        pytest.skip("sample absent")
    path = found[0]
    return path, funnel_days.parse(path)


def _group_week_total(path, group_key, label, week):
    """Value in the group's own (pivot subtotal) row, in the week-total column of block `label`."""
    rows = iter_rows(path, SHEET)
    _, sub = find_row(rows, "группа", "сотр")
    start = next(j for j, v in enumerate(sub) if isinstance(v, str) and v.startswith(label))
    dates = next(rows)
    col = next(j for j in range(start, start + 30) if str(dates[j]) == week)
    for r in rows:
        if r[1] == 1 and match_group(r[6]) == group_key:
            return num(r[col])
    raise AssertionError("group row not found")


def test_quality_invoices_reconcile_with_group_row(parsed):
    path, res = parsed
    week_days = {f"2026-11-0{d}" for d in range(2, 7)}
    mine = sum(f.num for f in res.facts if f.metric == "quality_invoices" and f.group == "СР1" and f.period in week_days)
    assert mine == _group_week_total(path, "СР1", "Качественные счета, шт.", "2026.45")


def test_groups_and_data_date(parsed):
    _, res = parsed
    groups = {f.group for f in res.facts}
    assert "СР9" in groups and "СР1" in groups
    assert res.data_date == date(2026, 11, 6)
    metrics = {f.metric for f in res.facts}
    assert {"staff", "quality_invoices", "long_presentations", "taken", "completed"} <= metrics


def test_no_plan_no_presence(parsed):
    _, res = parsed
    # 4 November is a public holiday: nobody has a plan, so nobody counts as present
    assert not [f for f in res.facts if f.period == "2026-11-04" and f.metric in ("staff", "quality_invoices")]


def test_staff_is_one_per_present_day(parsed):
    _, res = parsed
    staff = [f for f in res.facts if f.metric == "staff"]
    assert staff and all(f.num == 1 and f.den == 1 and f.employee for f in staff)
