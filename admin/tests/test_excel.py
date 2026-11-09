from datetime import date, datetime

import openpyxl

from npsr_admin.excel import excel_date, find_row, iter_rows


def _xlsx(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Свод"
    ws.append(["фильтр", "(Все)"])
    ws.append([])
    ws.append([None, "Ноябрь 2026"])
    ws.append([])
    ws.append([None, None, "Директор", "Филиал", "Группа"])
    ws.append([None, None, "АП", "Директор Д", "КЦПК_НП_СР_Тверь_СР1_ГБ"])
    path = tmp_path / "t.xlsx"
    wb.save(path)
    return path


def test_find_row_by_labels(tmp_path):
    rows = iter_rows(_xlsx(tmp_path), "Свод")
    idx, row = find_row(rows, "Директор", "Группа")
    assert idx == 4
    assert row[2] == "Директор"


def test_find_row_missing_returns_none(tmp_path):
    assert find_row(iter_rows(_xlsx(tmp_path), "Свод"), "Нет такого") is None


def test_excel_date():
    assert excel_date(46332.0) == date(2026, 11, 6)
    assert excel_date(datetime(2026, 11, 6, 0, 0)) == date(2026, 11, 6)
    assert excel_date("2026-11-06") == date(2026, 11, 6)
    assert excel_date("2026-11-06 00:00:00") == date(2026, 11, 6)
    assert excel_date("Итого") is None
    assert excel_date(3.0) is None  # small numbers are counters, not dates


def test_xlsb_header(sample):
    rows = iter_rows(sample("Опер_отчет_2026119.xlsb"), "Свод")
    found = find_row(rows, "Директор", "Филиал", "Группа", "Сотрудник")
    assert found is not None
