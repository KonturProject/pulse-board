import json
import subprocess

from npsr_admin.config import load_config
from npsr_admin.crypto import decrypt_json
from npsr_admin.publish import change_phrase, publish, share_link


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


def _repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "README.md").write_text("x")
    (repo / ".gitignore").write_text("web/public/data/\n*.xlsb\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "init")
    return repo


def test_publish_commits_only_encrypted_data(tmp_path):
    repo = _repo(tmp_path)
    (repo / "Опер_отчет_x.xlsb").write_bytes(b"secret")
    cfg = load_config()
    cfg.repo_dir = str(repo)
    payload = {"schemaVersion": 1, "dataDate": "2026-11-06", "values": {"x": {"2026.45": {"dir": 1}}}}
    res = publish(payload, cfg, push=False)
    files = _git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert sorted(files) == ["web/public/data/dashboard.enc.json", "web/public/data/version.json"]
    assert res.commit and _git(repo, "log", "-1", "--format=%s").strip() == "data: 2026-11-06"
    env = json.loads((repo / "web/public/data/dashboard.enc.json").read_text(encoding="utf-8"))
    assert decrypt_json(env, load_config().phrase) == payload
    version = json.loads((repo / "web/public/data/version.json").read_text(encoding="utf-8"))
    assert len(version["rev"]) == 64


def test_share_link_and_phrase_change(tmp_path):
    cfg = load_config()
    cfg.site_url = "https://konturproject.github.io/pulse-board/"
    old = change_phrase(cfg)
    new = change_phrase(cfg)
    assert old != new and load_config().phrase == new
    assert share_link(load_config()) == f"https://konturproject.github.io/pulse-board/#/?k={new}"


def test_push_only_from_main(tmp_path):
    import pytest

    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "-b", "feat")
    cfg = load_config()
    cfg.repo_dir = str(repo)
    with pytest.raises(RuntimeError, match="main"):
        publish({"dataDate": "2026-11-06"}, cfg, push=True)
