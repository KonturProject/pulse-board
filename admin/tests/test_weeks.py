from datetime import date

from npsr_admin.weeks import iso_week, last_working_day


def test_iso_week():
    assert iso_week(date(2026, 11, 2)) == "2026.45"
    assert iso_week(date(2026, 11, 8)) == "2026.45"
    assert iso_week(date(2026, 1, 1)) == "2026.01"


def test_last_working_day():
    assert last_working_day(date(2026, 11, 9)) == date(2026, 11, 6)  # Monday -> Friday
    assert last_working_day(date(2026, 11, 10)) == date(2026, 11, 9)
    assert last_working_day(date(2026, 11, 8)) == date(2026, 11, 6)  # Sunday -> Friday
