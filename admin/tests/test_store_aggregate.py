from datetime import date

import pytest

from npsr_admin.aggregate import build_payload
from npsr_admin.model import Fact, ParseResult
from npsr_admin.store import SourceInfo, Store

TODAY = date(2026, 11, 9)  # Monday -> data up to Friday 6 Nov, week 2026.45


def _store(tmp_path):
    return Store(tmp_path / "h.sqlite")


def test_save_same_day_twice_does_not_duplicate(tmp_path):
    s = _store(tmp_path)
    r = ParseResult("funnel", date(2026, 11, 6), [Fact("quality_invoices", "2026-11-06", "СР1", "Иванова", 3, 1)])
    s.save(r)
    s.save(r)
    assert len(s.facts(date(2026, 10, 1))) == 1


def test_save_recomputed_past_day_replaces_old(tmp_path):
    s = _store(tmp_path)
    s.save(ParseResult("funnel", date(2026, 11, 5), [Fact("quality_invoices", "2026-11-05", "СР1", "Иванова", 3, 1)]))
    s.save(ParseResult("funnel", date(2026, 11, 6), [
        Fact("quality_invoices", "2026-11-05", "СР1", "Иванова", 5, 1),
        Fact("quality_invoices", "2026-11-06", "СР1", "Иванова", 4, 1),
    ]))
    facts = {f.period: f.num for f in s.facts(date(2026, 10, 1))}
    assert facts == {"2026-11-05": 5, "2026-11-06": 4}
    assert s.sources()[0] == SourceInfo("funnel", date(2026, 11, 6), s.sources()[0].collected_at)


def _payload(facts, sources=()):
    return build_payload(list(facts), list(sources), {"quality_invoices": {"target": 4}}, TODAY)


def test_levels_are_sum_num_over_sum_den():
    p = _payload([
        Fact("quality_invoices", "2026-11-06", "СР1", "А", 3, 1),
        Fact("quality_invoices", "2026-11-06", "СР1", "Б", 5, 1),
        Fact("quality_invoices", "2026-11-06", "СР5", "В", 1, 1),
    ])
    day = p["values"]["quality_invoices"]["2026-11-06"]
    assert day["g:СР1"] == 4 and day["e:СР1:А"] == 3
    assert "br:Москва" not in day and "br:Тверь" not in day  # a single filial: no branch rows
    assert day["dir"] == pytest.approx(3)
    assert "g:СР2" not in day  # no facts -> absent, not zero
    assert p["entities"]["g:СР1"]["label"] == "СР1 ГБ"
    assert p["entities"]["e:СР1:А"] == {"label": "А", "group": "СР1"}


def test_week_to_date_and_week_values():
    p = _payload([
        Fact("quality_invoices", "2026-11-02", "СР1", "А", 2, 1),
        Fact("quality_invoices", "2026-11-04", "СР1", "А", 4, 1),
        Fact("quality_invoices", "2026-11-06", "СР1", "А", 6, 1),
    ])
    v = p["values"]["quality_invoices"]
    assert v["2026.45~2026-11-04"]["g:СР1"] == 3
    assert v["2026.45"]["g:СР1"] == 4
    assert p["days"]["2026.45"] == ["2026-11-02", "2026-11-04", "2026-11-06"]


def test_window_is_four_weeks():
    p = _payload([
        Fact("quality_invoices", "2026-10-09", "СР1", "А", 1, 1),  # 2026.41 — outside
        Fact("quality_invoices", "2026-10-16", "СР1", "А", 1, 1),  # 2026.42 — inside
    ])
    assert p["weeks"] == ["2026.42", "2026.43", "2026.44", "2026.45"]
    assert "2026-10-09" not in p["values"]["quality_invoices"]
    assert "2026-10-16" in p["values"]["quality_invoices"]


def test_group_level_facts_override_employee_sum_and_direction_star():
    p = _payload([
        Fact("runrate_money", "2026-11-06", "СР1", None, 120, 100),
        Fact("runrate_money", "2026-11-06", "СР1", "А", 50, 100),
        Fact("ns1_attempts", "2026.45", "*", None, 4.5, 1),
    ])
    assert p["values"]["runrate_money"]["2026-11-06"]["g:СР1"] == 1.2
    assert p["values"]["runrate_money"]["2026-11-06"]["e:СР1:А"] == 0.5
    assert p["values"]["ns1_attempts"]["2026.45"] == {"dir": 4.5}


def test_cumulative_runrate_week_value_is_last_day():
    p = _payload([
        Fact("runrate_money", "2026-11-05", "СР1", None, 80, 100),
        Fact("runrate_money", "2026-11-06", "СР1", None, 130, 100),
    ])
    assert p["values"]["runrate_money"]["2026.45"]["g:СР1"] == 1.3


def test_needs_staff_metrics_divide_by_week_staff():
    p = _payload([
        Fact("staff", "2026-11-05", "СР1", "А", 1, 1),
        Fact("staff", "2026-11-06", "СР1", "А", 1, 1),
        Fact("staff", "2026-11-06", "СР1", "Б", 1, 1),
        Fact("orders_extra_seats", "2026.45", "СР1", None, 6, 0),
        Fact("ak_robot_coverage", "2026.45", "СР1", "А", 1, 0),
    ])
    assert p["values"]["orders_extra_seats"]["2026.45"]["g:СР1"] == 3  # 6 invoices / 2 people
    assert p["values"]["ak_robot_coverage"]["2026.45"]["g:СР1"] == 0.5  # 1 of 2 people
    assert "e:СР1:А" not in p["values"]["ak_robot_coverage"]["2026.45"]


def test_robot_coverage_is_capped_at_100_percent():
    p = _payload([
        Fact("staff", "2026-11-06", "СР5", "А", 1, 1),
        Fact("ak_robot_coverage", "2026.45", "СР5", "А", 1, 0),
        Fact("ak_robot_coverage", "2026.45", "СР5", "Ученик без плана", 1, 0),
    ])
    assert p["values"]["ak_robot_coverage"]["2026.45"]["g:СР5"] == 1.0


def test_stale_sources():
    p = _payload([], [SourceInfo("oper", date(2026, 11, 6), "x"), SourceInfo("funnel", date(2026, 11, 4), "x"),
                      SourceInfo("gkg", None, "x")])
    st = {s["id"]: s["stale"] for s in p["sources"]}
    assert st == {"oper": False, "funnel": True, "gkg": False}
    assert p["dataDate"] == "2026-11-06"


# --- final review fixes ---

def test_empty_result_changes_nothing(tmp_path):
    s = _store(tmp_path)
    s.save(ParseResult("funnel", date(2026, 11, 5), [Fact("quality_invoices", "2026-11-05", "СР1", "А", 3, 1)]))
    s.save(ParseResult("funnel", None, [], ["лист не найден"]))
    assert len(s.facts(date(2026, 10, 1))) == 1
    assert s.sources()[0].data_date == date(2026, 11, 5)


def test_older_archive_does_not_move_data_date_back(tmp_path):
    s = _store(tmp_path)
    s.save(ParseResult("funnel", date(2026, 11, 6), [Fact("quality_invoices", "2026-11-06", "СР1", "А", 3, 1)]))
    s.save(ParseResult("funnel", date(2026, 10, 2), [Fact("quality_invoices", "2026-10-02", "СР1", "А", 1, 1)]))
    assert s.sources()[0].data_date == date(2026, 11, 6)
    assert len(s.facts(date(2026, 9, 1))) == 2


def test_missing_metric_keeps_its_history(tmp_path):
    s = _store(tmp_path)
    s.save(ParseResult("oper", date(2026, 11, 6), [Fact("runrate_money", "2026-11-06", "СР1", None, 1, 1),
                                                   Fact("runrate_pcs", "2026-11-06", "СР1", None, 2, 1)]))
    s.save(ParseResult("oper", date(2026, 11, 6), [Fact("runrate_money", "2026-11-06", "СР1", None, 5, 1)]))
    got = {(f.metric, f.num) for f in s.facts(date(2026, 10, 1))}
    assert got == {("runrate_money", 5), ("runrate_pcs", 2)}


def test_per_person_branch_counts_only_groups_present():
    p = _payload([
        Fact("staff", "2026-11-06", "СР1", "А", 1, 1),
        Fact("staff", "2026-11-06", "СР9", "Б", 1, 1),
        Fact("orders_extra_seats", "2026.45", "СР1", None, 4, 0),  # СР9 absent from the report
    ])
    v = p["values"]["orders_extra_seats"]["2026.45"]
    assert v["g:СР1"] == 4 and v["dir"] == 4  # СР9 staff does not dilute the direction


def test_data_date_is_last_day_with_daily_data_not_file_date():
    p = _payload([Fact("quality_invoices", "2026-11-06", "СР1", "А", 3, 1)],
                 [SourceInfo("funnel", date(2026, 11, 6), "x"), SourceInfo("ak", date(2026, 11, 9), "x")])
    assert p["dataDate"] == "2026-11-06"
