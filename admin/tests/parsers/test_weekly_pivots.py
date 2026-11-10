import pytest

from npsr_admin.parsers import attempts300, gkg


def _ratio(facts):
    return sum(f.num for f in facts) / sum(f.den for f in facts)


def test_gkg_reads_pivot_cache_down_to_employees(sample):
    res = gkg.parse(sample("АП_НП_СР_Воронка_ГкГ_НС.xlsb"))
    cur = [f for f in res.facts if f.metric == "ns1_attempts" and f.period == "2026.45"]
    # the sheet's pivot hides СР9 ГБА: without it the cache gives exactly the pivot's 1155 / 256 = 4.5117
    assert _ratio([f for f in cur if f.group != "СР9"]) == pytest.approx(4.51171875)
    assert {f.group for f in cur} == {"СР1", "СР2", "СР3", "СР5", "СР6", "СР9"}
    assert all(f.employee for f in cur) and len({f.employee for f in cur}) > 20
    ly = [f for f in res.facts if f.metric == "ns1_attempts_ly" and f.period == "2026.45"]
    # last year's direction includes groups closed since (СР4, Москва) — the pivot's 3.4523
    assert _ratio([f for f in ly if f.group == "*"]) == pytest.approx(3.4522821576763487)
    assert {f.group for f in ly} >= {"*", "СР2", "СР3"}
    assert all(f.employee is None for f in ly)  # last year's people must not appear as rows
    assert not any("свёрнута" in w for w in res.warnings)


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
