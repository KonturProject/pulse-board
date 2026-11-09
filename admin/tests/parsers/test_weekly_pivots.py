import pytest

from npsr_admin.parsers import attempts300, gkg


def test_gkg_collapsed_pivot_gives_direction_level_ns1(sample):
    res = gkg.parse(sample("АП_НП_СР_Воронка_ГкГ_НС.xlsb"))
    cur = [f for f in res.facts if f.metric == "ns1_attempts" and f.period == "2026.45"]
    assert len(cur) == 1 and cur[0].group == "*" and cur[0].employee is None
    assert cur[0].num / cur[0].den == pytest.approx(4.51171875)
    ly = [f for f in res.facts if f.metric == "ns1_attempts_ly" and f.period == "2026.45"]
    assert ly[0].num / ly[0].den == pytest.approx(3.4522821576763487)
    assert any("свёрнута" in w for w in res.warnings)


def test_attempts300_reconciles_with_total(sample):
    res = attempts300.parse(sample("3.3. Попытки в 300+.xlsx"))
    wk = [f for f in res.facts if f.metric == "attempts_300" and f.period == "2026.45"]
    assert sum(f.num for f in wk) / sum(f.den for f in wk) == pytest.approx(3.4130288784419074)
    groups = {f.group for f in res.facts}
    assert groups == {"СР1", "СР2", "СР3", "СР5", "СР6"}
    assert all(f.employee is None for f in res.facts)


def test_attempts300_survives_a_shifted_pivot(tmp_path):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "НП СР по менеджерам"
    ws.append([None, "300+"])
    ws.append([None, None, "Кол-во звонков", None, "Кол-во перезвонов"])
    ws.append([None, "Названия строк", "2026.44", "2026.45", "2026.44", "2026.45"])
    ws.append([None, "КЦПК_НП_СР_Тверь_СР1_ГБ", 10, 20, 30, 70])
    path = tmp_path / "300.xlsx"
    wb.save(path)
    res = attempts300.parse(path)
    wk = {f.period: f.num / f.den for f in res.facts}
    assert wk == {"2026.44": 3.0, "2026.45": 3.5}
