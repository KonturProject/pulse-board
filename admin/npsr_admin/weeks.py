"""Aktion lives in ISO weeks written as `2026.45`; reports are built "up to yesterday"."""

from datetime import date, timedelta


def iso_week(d: date) -> str:
    year, week, _ = d.isocalendar()
    return f"{year}.{week:02d}"


def last_working_day(today: date) -> date:
    """The last weekday strictly before `today` (holidays are not tracked)."""
    d = today - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def week_days(week: str) -> list[date]:
    """Monday..Sunday of an ISO week `YYYY.WW`."""
    year, num = (int(x) for x in week.split("."))
    monday = date.fromisocalendar(year, num, 1)
    return [monday + timedelta(days=i) for i in range(7)]
