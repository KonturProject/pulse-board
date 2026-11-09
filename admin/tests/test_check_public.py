import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "check_public", Path(__file__).resolve().parents[2] / "scripts" / "check_public.py"
)
check_public = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_public)


def test_rejects_excel():
    assert check_public.main(["a/Опер_отчет.xlsb", "web/src/App.tsx"]) == 1
    assert check_public.main(["x/report.XLSX"]) == 1


def test_rejects_local_state():
    assert check_public.main([".superpowers/brainstorm/x.html"]) == 1
    assert check_public.main(["history.sqlite"]) == 1
    assert check_public.main(["admin/config.json"]) == 1


def test_accepts_published_data():
    assert check_public.main(["web/public/data/dashboard.enc.json", "web/public/data/version.json"]) == 0
