"""Uniform streaming access to .xlsx / .xlsm / .xlsb sheets.

Reports are pivot tables with filters above them, so headers float: find them by text, never by fixed
coordinates.
"""

from collections.abc import Iterable, Iterator
from datetime import date, datetime, timedelta
from pathlib import Path

import openpyxl
from pyxlsb import open_workbook

_EXCEL_EPOCH = date(1899, 12, 30)


def sheet_names(path: Path) -> list[str]:
    if Path(path).suffix.lower() == ".xlsb":
        with open_workbook(str(path)) as wb:
            return list(wb.sheets)
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        return wb.sheetnames
    finally:
        wb.close()


def iter_rows(path: Path, sheet: str, max_col: int | None = None) -> Iterator[list[object]]:
    """Cell values row by row. Raises KeyError if the sheet does not exist."""
    if Path(path).suffix.lower() == ".xlsb":
        with open_workbook(str(path)) as wb:
            if sheet not in wb.sheets:
                raise KeyError(sheet)
            with wb.get_sheet(sheet) as sh:
                for row in sh.rows():
                    vals = [c.v for c in row]
                    yield vals[:max_col] if max_col else vals
        return
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        if sheet not in wb.sheetnames:
            raise KeyError(sheet)
        for row in wb[sheet].iter_rows(values_only=True, max_col=max_col):
            yield list(row)
    finally:
        wb.close()


def find_row(rows: Iterable[list], *labels: str, limit: int = 60) -> tuple[int, list] | None:
    """First row (index, values) among the first `limit` that contains every label as a substring
    of some cell."""
    for i, row in enumerate(rows):
        if i >= limit:
            return None
        texts = [v for v in row if isinstance(v, str)]
        if all(any(label in t for t in texts) for label in labels):
            return i, row
    return None


def excel_date(v: object) -> date | None:
    """A date from an Excel serial number, a datetime or an ISO-like string; None otherwise."""
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if 40000 <= v <= 60000:  # 2009..2064 — anything else is a counter, not a date
            return _EXCEL_EPOCH + timedelta(days=int(v))
        return None
    if isinstance(v, str):
        try:
            return date.fromisoformat(v.strip()[:10])
        except ValueError:
            return None
    return None


def num(v: object) -> float:
    """Numeric cell value; blanks, dashes and text count as 0."""
    if isinstance(v, bool):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.replace(",", ".").replace("\xa0", "").replace(" ", ""))
        except ValueError:
            return 0.0
    return 0.0
