"""Local admin web app: http://127.0.0.1:<port>/ — collect reports, review, publish, edit norms, get the link.

Listens on 127.0.0.1 only and refuses requests whose Host is not local (DNS-rebinding guard).
"""

import http.client
import json
import os
import subprocess
import threading
import time
from dataclasses import asdict
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .aggregate import build_payload
from .collect import collect
from .config import REPORT_NAMES, Config, ReportCfg, home, load_config, save_config
from .publish import change_phrase, publish, share_link
from .store import Store

UI_DIR = Path(__file__).parent / "ui"
REPO_DIR = Path(__file__).resolve().parents[2]


def code_version() -> str:
    """Last commit of the running code — shown in the admin so an outdated copy is easy to spot."""
    try:
        out = subprocess.run(["git", "-C", str(REPO_DIR), "log", "-1", "--format=%h от %cd", "--date=format:%d.%m.%Y %H:%M"],
                             capture_output=True, text=True, encoding="utf-8", timeout=5)
        return out.stdout.strip() or "неизвестна"
    except (OSError, subprocess.SubprocessError):
        return "неизвестна"


VERSION = code_version()
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                 ".css": "text/css; charset=utf-8"}


class State:
    def __init__(self):
        self.lock = threading.Lock()
        self.running = False
        self.log: list[str] = []
        self.items: list[dict] = []
        self.uploads: dict[str, Path] = {}
        self.store = Store(home() / "history.sqlite")

    def payload(self, cfg: Config) -> dict:
        today = date.today()
        facts = self.store.facts(today - timedelta(days=45))
        return build_payload(facts, self.store.sources(), cfg.norms, today, cfg.duck_threshold,
                             {k: r.allowed_lag for k, r in cfg.reports.items()})


def _config_json(cfg: Config) -> dict:
    data = asdict(cfg)
    data["names"] = REPORT_NAMES
    data["link"] = share_link(cfg) if cfg.phrase else None
    data["version"] = VERSION
    return data


class Handler(BaseHTTPRequestHandler):
    state: State

    def log_message(self, *args):  # keep the console quiet
        pass

    def _send(self, status: int, body, ctype="application/json; charset=utf-8"):
        data = json.dumps(body, ensure_ascii=False, default=str).encode() if ctype.startswith("application/json") else body
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _local(self, write: bool = False) -> bool:
        """Host must be local (DNS rebinding); writes must also come from the admin page itself (CSRF)."""
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        ok = host in ("127.0.0.1", "localhost")
        if ok and write:
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).hostname not in ("127.0.0.1", "localhost"):
                ok = False
            if self.headers.get("Sec-Fetch-Site") in ("cross-site", "same-site"):
                ok = False
        if not ok:
            self._send(403, {"error": "только локальный доступ"})
        return ok

    def _body(self) -> bytes:
        return self.rfile.read(int(self.headers.get("Content-Length") or 0))

    def do_GET(self):
        if not self._local():
            return
        path = urlparse(self.path).path
        st = self.state
        if path == "/api/config":
            return self._send(200, _config_json(load_config()))
        if path == "/api/progress":
            with st.lock:
                return self._send(200, {"running": st.running, "log": st.log[-200:], "items": st.items,
                                        "uploads": {k: v.name for k, v in st.uploads.items()}})
        if path == "/api/preview":
            return self._send(200, st.payload(load_config()))
        name = "index.html" if path in ("/", "") else path.lstrip("/")
        file = (UI_DIR / name).resolve()
        if file.parent == UI_DIR.resolve() and file.is_file():
            return self._send(200, file.read_bytes(), CONTENT_TYPES.get(file.suffix, "application/octet-stream"))
        self._send(404, {"error": "нет такой страницы"})

    def do_PUT(self):
        if not self._local(write=True):
            return
        if urlparse(self.path).path != "/api/config":
            return self._send(404, {"error": "нет такого адреса"})
        data = json.loads(self._body() or b"{}")
        cfg = load_config()
        for k, r in data.get("reports", {}).items():
            cfg.reports[k] = ReportCfg(r.get("folder", ""), r.get("pattern", ""), int(r.get("allowed_lag", 1)))
        if "norms" in data:
            cfg.norms = data["norms"]
        cfg.duck_threshold = float(data.get("duck_threshold", cfg.duck_threshold))
        cfg.site_url = data.get("site_url", cfg.site_url)
        save_config(cfg)
        self._send(200, _config_json(cfg))

    def do_POST(self):
        if not self._local(write=True):
            return
        url = urlparse(self.path)
        st = self.state
        if url.path == "/api/collect":
            with st.lock:
                if st.running:
                    return self._send(409, {"error": "сбор уже идёт"})
                st.running, st.log, st.items = True, [], []
            threading.Thread(target=self._collect, daemon=True).start()
            return self._send(202, {"ok": True})
        if url.path == "/api/upload":
            source = parse_qs(url.query).get("source", [""])[0]
            name = parse_qs(url.query).get("name", ["file.xlsx"])[0]
            if source not in load_config().reports:
                return self._send(400, {"error": "неизвестный отчёт"})
            target = home() / "uploads" / f"{source}{Path(name).suffix.lower()}"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self._body())
            with st.lock:
                st.uploads[source] = target
            return self._send(200, {"ok": True, "file": name})
        if url.path == "/api/publish":
            cfg = load_config()
            try:
                res = publish(st.payload(cfg), cfg, push=True)
            except Exception as e:  # noqa: BLE001 — show any git/publish problem to the user
                return self._send(500, {"error": f"{type(e).__name__}: {e}"})
            return self._send(200, {"commit": res.commit, "link": share_link(load_config())})
        if url.path == "/api/shutdown":  # a newer start of the admin takes over the address
            self._send(200, {"ok": True})
            srv = self.server

            def stop():
                srv.shutdown()
                srv.server_close()  # free the address, not only stop serving

            threading.Thread(target=stop, daemon=True).start()
            return
        if url.path == "/api/phrase":
            cfg = load_config()
            change_phrase(cfg)
            try:  # spec: a new phrase re-encrypts the published data at once
                publish(st.payload(cfg), cfg, push=True)
                warning = None
            except Exception as e:  # noqa: BLE001
                warning = f"Код сменён, но публикация не прошла: {e}. Нажмите «Опубликовать»."
            return self._send(200, {"link": share_link(cfg), "warning": warning})
        self._send(404, {"error": "нет такого адреса"})

    def _collect(self):
        st = self.state

        def progress(msg: str):
            with st.lock:
                st.log.append(msg)

        try:
            with st.lock:
                uploads = dict(st.uploads)
            items = collect(load_config(), st.store, files=uploads, progress=progress)
            with st.lock:
                st.items = [asdict(i) for i in items]
                st.uploads = {}
        finally:
            with st.lock:
                st.running = False


class Server(ThreadingHTTPServer):
    # Windows would otherwise let a second admin bind the same port silently and share requests with an
    # old one still running in the background (pythonw has no window) — exactly how stale code got used.
    allow_reuse_address = False


def _ask_old_to_stop(port: int) -> None:
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
        conn.request("POST", "/api/shutdown", body=b"{}", headers={"Host": f"127.0.0.1:{port}"})
        conn.getresponse().read()
    except OSError:
        pass


def _kill_old_python(port: int) -> None:
    """An admin too old to know /api/shutdown: stop the Python process listening on the port (Windows)."""
    if os.name != "nt":
        return
    try:
        out = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True, timeout=10).stdout
        pids = {int(line.split()[-1]) for line in out.splitlines()
                if f"127.0.0.1:{port} " in line and "LISTENING" in line}
        for pid in pids - {os.getpid()}:
            name = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                                  capture_output=True, text=True, timeout=10).stdout.lower()
            if "python" in name:
                subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError, ValueError):
        pass


def _bind(port: int, handler) -> Server | None:
    try:
        return Server(("127.0.0.1", port), handler)
    except OSError:
        return None


def make_server(port: int = 8765) -> ThreadingHTTPServer:
    """Start serving in a background thread; port 0 picks a free port."""
    handler = type("BoundHandler", (Handler,), {"state": State()})
    srv = _bind(port, handler) if port else None
    if srv is None and port:
        for attempt in (_ask_old_to_stop, _kill_old_python):  # an older admin holds the address
            attempt(port)
            for _ in range(15):
                time.sleep(0.2)
                srv = _bind(port, handler)
                if srv:
                    break
            if srv:
                break
    if srv is None:
        srv = Server(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
