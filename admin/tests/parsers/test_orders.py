import pytest

from npsr_admin.parsers import orders

# «Общий итог» of week 45 in each sheet of the sample (from the pivot itself)
TOTALS_W45 = {"orders_extra_seats": 154, "orders_schools": 57, "orders_periodicals": 47}


@pytest.fixture(scope="module")
def parsed():
    from tests.conftest import SAMPLES_DIR

    path = SAMPLES_DIR / "АП_Свод_по_заказам.xlsb"
    if not path.exists():
        pytest.skip("sample absent")
    return orders.parse(path)


@pytest.mark.parametrize("metric", sorted(TOTALS_W45))
def test_group_counts_reconcile_with_total(parsed, metric):
    week = [f for f in parsed.facts if f.metric == metric and f.period.endswith(".45")]
    assert sum(f.num for f in week) == TOTALS_W45[metric]
    assert {f.group for f in week} == {"СР1", "СР2", "СР3", "СР5", "СР6", "СР9"}
    assert all(f.employee is None and f.den == 0 for f in week)
