import os
from datetime import date
from pathlib import Path

from npsr_admin import collect as collect_mod
from npsr_admin.collect import collect, find_latest
from npsr_admin.config import ReportCfg, load_config, save_config
from npsr_admin.model import Fact, ParseResult
from npsr_admin.store import Store


def test_config_round_trip_and_defaults(npsr_home):
    cfg = load_config()
    assert set(cfg.reports) == {"oper", "funnel", "gkg", "attempts300", "ak", "orders", "oz_speed", "oz_attempts"}
    assert cfg.reports["oper"].pattern == "Опер_отчет_*.xlsb"
    assert cfg.norms["quality_invoices"] == {"target": 4}
    assert cfg.norms["oz_speed_30"] == {"target": 0.95}
    assert cfg.duck_threshold == 0.15
    cfg.reports["oper"].folder = r"\\server\reports\oper"
    save_config(cfg)
    assert load_config().reports["oper"].folder == r"\\server\reports\oper"
    assert (npsr_home / "config.json").exists()


def test_find_latest_picks_newest(tmp_path):
    old = tmp_path / "Опер_отчет_2026118.xlsb"
    new = tmp_path / "Опер_отчет_2026119.xlsb"
    for i, p in enumerate((old, new)):
        p.write_bytes(b"x")
        os.utime(p, (1_000_000 + i * 100, 1_000_000 + i * 100))
    (tmp_path / "Другой.xlsb").write_bytes(b"x")
    assert find_latest(tmp_path, "Опер_отчет_*.xlsb") == new
    assert find_latest(tmp_path, "Нет_*.xlsb") is None


def _stub_registry(monkeypatch):
    def ok(path):
        return ParseResult("oper", date(2026, 11, 6), [Fact("runrate_money", "2026-11-06", "СР1", None, 1, 1)])

    def boom(path):
        raise ValueError("сломанный файл")

    monkeypatch.setattr(collect_mod, "REGISTRY", {"oper": ok, "funnel": boom})


def test_collect_isolates_failures(tmp_path, monkeypatch):
    _stub_registry(monkeypatch)
    folder = tmp_path / "share"
    folder.mkdir()
    (folder / "Опер_отчет_1.xlsb").write_bytes(b"x")
    (folder / "АП_НП_СР_Воронка_Дни_x.xlsx").write_bytes(b"x")
    cfg = load_config()
    cfg.reports = {"oper": ReportCfg(str(folder), "Опер_отчет_*.xlsb"),
                   "funnel": ReportCfg(str(folder), "АП_НП_СР_Воронка_Дни*.xlsx"),
                   "gkg": ReportCfg(str(tmp_path / "missing"), "x*.xlsb")}
    store = Store(tmp_path / "h.sqlite")
    items = {i.source: i for i in collect(cfg, store, progress=lambda m: None)}
    assert items["oper"].error is None and items["oper"].data_date == date(2026, 11, 6)
    assert "сломанный файл" in items["funnel"].error
    assert items["gkg"].error == f"папка недоступна: {tmp_path / 'missing'}"
    assert len(store.facts(date(2026, 10, 1))) == 1


def test_collect_manual_file_overrides_folder(tmp_path, monkeypatch):
    _stub_registry(monkeypatch)
    manual = tmp_path / "dropped.xlsb"
    manual.write_bytes(b"x")
    cfg = load_config()
    cfg.reports = {"oper": ReportCfg("", "Опер_отчет_*.xlsb")}
    items = collect(cfg, Store(tmp_path / "h.sqlite"), files={"oper": manual}, progress=lambda m: None)
    assert items[0].error is None and Path(items[0].file).name == "dropped.xlsb"


def test_zero_facts_is_a_warning_and_weekly_date_is_file_date(tmp_path, monkeypatch):
    def empty(path):
        return ParseResult("gkg", None, [], [])

    def weekly(path):
        return ParseResult("ak", None, [Fact("ak_rg_feedback", "2026.45", "СР1", None, 1, 1)], [])

    monkeypatch.setattr(collect_mod, "REGISTRY", {"gkg": empty, "ak": weekly})
    folder = tmp_path / "share"
    folder.mkdir()
    (folder / "g.xlsb").write_bytes(b"x")
    ak_file = folder / "a.xlsb"
    ak_file.write_bytes(b"x")
    ts = __import__("datetime").datetime(2026, 11, 6, 7, 0).timestamp()
    os.utime(ak_file, (ts, ts))
    cfg = load_config()
    cfg.reports = {"gkg": ReportCfg(str(folder), "g*.xlsb"), "ak": ReportCfg(str(folder), "a*.xlsb")}
    items = {i.source: i for i in collect(cfg, Store(tmp_path / "h.sqlite"), progress=lambda m: None)}
    assert any("0 записей" in w for w in items["gkg"].warnings)
    assert items["ak"].data_date == date(2026, 11, 6)
