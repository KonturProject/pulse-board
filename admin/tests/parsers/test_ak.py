import time

import openpyxl
import pytest

from npsr_admin.parsers import ak

HEADER = [
    "_ Оценка по критерию", "_ Количество оценок по критерию", "М Руководитель направления", "М Филиал",
    "М Подразделение", "М Менеджер", "М Новая должность", "t Неделя относительная", "t Год", "t Месяц",
    "t Неделя", "t Неделя звонка", "t Дата", "АК Тип подразделения", "АК Подразделение аудиоконтроля",
    "АК Менеджер аудиоконтроля", "Ученическая группа", "АК Карта качества", "АК Тип критерия", "АК Критерий оценки",
]
G1 = "КЦПК_НП_СР_Тверь_СР1_ГБ"
G2 = "КЦПК_НП_СР_Тверь_СР2_Фин"


def _row(score, dept, manager, card, ctype, week=2026.45):
    r = [None] * len(HEADER)
    r[0], r[1], r[4], r[5], r[10], r[17], r[18] = score, 1, dept, manager, week, card, ctype
    return r


@pytest.fixture
def ak_file(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DATA_po_kriter"
    ws.append(["Из БД:", "[PressAP].[st].[audio_kontrol]"])
    ws.append([])
    ws.append(HEADER)
    for r in [
        _row(100, G1, "Руководитель А", "АП_ОС_Практика_РГ 2.0", "1. Тема ОС"),
        _row(50, G1, "Руководитель А", "АП_ОС_Практика_РГ 2.0", "2. Прослушка звонка"),
        _row(100, G1, "Иванова", "АП_МП_Оценка робота", "3. Срок оплаты"),
        _row(0, G1, "Петрова", "АП_МП_Оценка робота", "3. Срок оплаты"),
        _row(100, G1, "Петрова", "Оценка робота_НС_new", "3. Срок оплаты"),
        _row(100, G1, "Иванова", "АП_МП_Оценка робота", "1. Установление контакта"),
        _row(100, G2, "Сидорова", "АП_НП_первичка", "3. Срок оплаты"),
        _row(100, "КЦПК_НП_СР_Тверь_Ученики", "Ученик", "АП_МП_Оценка робота", "3. Срок оплаты"),
    ]:
        ws.append(r)
    path = tmp_path / "ak.xlsx"
    wb.save(path)
    return path


def _facts(res, metric):
    return [f for f in res.facts if f.metric == metric]


def test_rg_feedback_is_group_level_average(ak_file):
    fs = _facts(ak.parse(ak_file), "ak_rg_feedback")
    assert all(f.employee is None and f.group == "СР1" and f.period == "2026.45" for f in fs)
    assert sum(f.num for f in fs) / sum(f.den for f in fs) == pytest.approx(75)


def test_robot_coverage_counts_unique_managers(ak_file):
    fs = _facts(ak.parse(ak_file), "ak_robot_coverage")
    assert sorted(f.employee for f in fs) == ["Иванова", "Петрова"]
    assert all(f.num == 1 and f.den == 0 for f in fs)


def test_pay_term_share_of_100(ak_file):
    res = ak.parse(ak_file)
    prim = _facts(res, "ak_pay_term_primary")
    assert sum(f.num for f in prim) / sum(f.den for f in prim) == pytest.approx(0.5)
    ns = _facts(res, "ak_pay_term_ns")
    assert sum(f.num for f in ns) / sum(f.den for f in ns) == pytest.approx(1.0)
    assert {f.group for f in res.facts} == {"СР1"}


def test_real_file_has_every_metric_in_time(sample):
    path = sample("АП_НП_СР_АК.xlsb")
    t = time.monotonic()
    res = ak.parse(path)
    assert time.monotonic() - t < 120
    metrics = {f.metric for f in res.facts}
    assert {"ak_rg_feedback", "ak_robot_coverage", "ak_pay_term_primary", "ak_pay_term_ns"} <= metrics
