"""Local admin config (folders of reports, norms, access phrase) — kept outside the repository.

Location: $NPSR_HOME, else %LOCALAPPDATA%\\npsr-dashboard.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[2]

DEFAULT_PATTERNS = {
    "oper": "Опер_отчет_*.xlsb",
    "funnel": "АП_НП_СР_Воронка_Дни*.xlsx",
    "gkg": "АП_НП_СР_Воронка_ГкГ_НС*.xlsb",
    "attempts300": "*Попытки в 300+*.xlsx",
    "ak": "АП_НП_СР_АК*.xlsb",
    "orders": "АП_Свод_по_заказам*.xlsb",
    "oz_speed": "АП_НП_Обратный звонок_new*.xlsm",
    "oz_attempts": "АП_НП_СР_Попытки в первичке ПИНы_ОЗ*.xlsx",
}

REPORT_NAMES = {
    "oper": "Опер_отчет",
    "funnel": "Воронка по дням",
    "gkg": "Воронка ГкГ (НС)",
    "attempts300": "Попытки в 300+",
    "ak": "Аудиоконтроль",
    "orders": "Свод по заказам",
    "oz_speed": "Обратный звонок",
    "oz_attempts": "Попытки ОЗ (ПИНы)",
}

# Values are in the metric's own units (run-rate 1.0 = 100%, shares 0..1).
DEFAULT_NORMS = {
    "runrate_money": {"target": 1.0, "tiers": [1.0, 1.2, 1.4]},
    "runrate_pcs": {"target": 1.0, "tiers": [1.0, 1.2, 1.4]},
    "quality_invoices": {"target": 4},
    "long_presentations": {"floor": 1.2, "target": 1.5},
    "ns1_attempts": {"target": 5},
    "attempts_300": {"target": 3.8},
    "oz_attempts": {"target": 6.5},
    "oz_speed_30": {"target": 0.95},
}


@dataclass
class ReportCfg:
    folder: str = ""
    pattern: str = ""
    allowed_lag: int = 1


@dataclass
class Config:
    reports: dict[str, ReportCfg] = field(
        default_factory=lambda: {k: ReportCfg("", p) for k, p in DEFAULT_PATTERNS.items()})
    norms: dict = field(default_factory=lambda: json.loads(json.dumps(DEFAULT_NORMS)))
    duck_threshold: float = 0.15
    phrase: str | None = None
    repo_dir: str = str(REPO_DIR)
    site_url: str = ""


def home() -> Path:
    base = os.environ.get("NPSR_HOME") or str(Path(os.environ.get("LOCALAPPDATA", Path.home())) / "npsr-dashboard")
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_config() -> Config:
    path = home() / "config.json"
    cfg = Config()
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        for k, r in data.get("reports", {}).items():
            cfg.reports[k] = ReportCfg(**r)
        cfg.norms.update(data.get("norms", {}))
        cfg.duck_threshold = data.get("duck_threshold", cfg.duck_threshold)
        cfg.phrase = data.get("phrase")
        cfg.repo_dir = data.get("repo_dir", cfg.repo_dir)
        cfg.site_url = data.get("site_url", cfg.site_url)
    return cfg


def save_config(cfg: Config) -> None:
    (home() / "config.json").write_text(json.dumps(asdict(cfg), ensure_ascii=False, indent=2), encoding="utf-8")
