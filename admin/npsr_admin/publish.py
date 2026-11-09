"""Encrypt the payload and commit/push exactly two files to the public repository.

`web/public/data/dashboard.enc.json` — the encrypted payload; `web/public/data/version.json` — open,
only the fingerprint and time, so viewers re-download data only when it changed.
"""

import hashlib
import importlib.util
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import Config, save_config
from .crypto import encrypt_json, new_salt
from .phrase import new_phrase

DATA_DIR = "web/public/data"
ENC = f"{DATA_DIR}/dashboard.enc.json"
VERSION = f"{DATA_DIR}/version.json"


@dataclass
class PublishResult:
    commit: str | None
    files: list[str]


def _check_public(repo: Path, paths: list[str]) -> None:
    spec = importlib.util.spec_from_file_location("check_public", Path(__file__).resolve().parents[2] / "scripts" / "check_public.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if mod.main(paths) != 0:
        raise RuntimeError("публикация остановлена: среди файлов есть запрещённые")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True, encoding="utf-8").stdout


def change_phrase(cfg: Config) -> str:
    cfg.phrase = new_phrase()
    save_config(cfg)
    return cfg.phrase


def share_link(cfg: Config) -> str:
    base = cfg.site_url or "https://konturproject.github.io/<репозиторий>/"
    if not base.endswith("/"):
        base += "/"
    return f"{base}#/?k={cfg.phrase}"


def publish(payload: dict, cfg: Config, push: bool = True) -> PublishResult:
    if not cfg.phrase:
        change_phrase(cfg)
    repo = Path(cfg.repo_dir)
    if push and _git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip() != "main":
        raise RuntimeError("публикация возможна только из ветки main (с неё собирается сайт)")
    env = encrypt_json(payload, cfg.phrase, new_salt())
    body = json.dumps(env, separators=(",", ":"))
    version = {"rev": hashlib.sha256(body.encode()).hexdigest(), "generatedAt": datetime.now().isoformat(timespec="seconds")}
    (repo / DATA_DIR).mkdir(parents=True, exist_ok=True)
    (repo / ENC).write_text(body, encoding="utf-8")
    (repo / VERSION).write_text(json.dumps(version), encoding="utf-8")
    files = [ENC, VERSION]
    _check_public(repo, files)
    _git(repo, "add", "-f", "--", *files)  # data dir is gitignored for local dev builds
    _git(repo, "commit", "-m", f"data: {payload.get('dataDate') or version['generatedAt'][:10]}", "--", *files)
    commit = _git(repo, "rev-parse", "HEAD").strip()
    if push:
        _git(repo, "push")
    return PublishResult(commit, files)
