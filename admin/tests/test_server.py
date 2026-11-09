import http.client
import json
import time

import pytest

from npsr_admin.server import make_server


@pytest.fixture
def server():
    srv = make_server(port=0)
    yield srv
    srv.shutdown()


def _req(srv, method, path, body=None, host=None):
    port = srv.server_address[1]
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    headers = {"Host": host or f"127.0.0.1:{port}", "Content-Type": "application/json"}
    conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=headers)
    res = conn.getresponse()
    data = res.read()
    return res.status, (json.loads(data) if res.getheader("Content-Type", "").startswith("application/json") else data)


def test_config_put_then_get(server):
    status, cfg = _req(server, "GET", "/api/config")
    assert status == 200 and "oper" in cfg["reports"]
    cfg["reports"]["oper"]["folder"] = r"\\server\reports\oper"
    assert _req(server, "PUT", "/api/config", cfg)[0] == 200
    assert _req(server, "GET", "/api/config")[1]["reports"]["oper"]["folder"] == r"\\server\reports\oper"


def test_collect_with_no_folders_reports_errors_for_all(server):
    assert _req(server, "POST", "/api/collect", {})[0] == 202
    for _ in range(50):
        status, prog = _req(server, "GET", "/api/progress")
        if not prog["running"] and prog["items"]:
            break
        time.sleep(0.1)
    assert len(prog["items"]) == 8
    assert all(i["error"] for i in prog["items"])


def test_rejects_foreign_host(server):
    assert _req(server, "GET", "/api/config", host="evil.example.com")[0] == 403


def test_serves_ui(server):
    status, body = _req(server, "GET", "/")
    assert status == 200 and "Собрать отчёты".encode() in body


def _post_with(srv, path, headers):
    port = srv.server_address[1]
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    conn.request("POST", path, body=b"{}", headers={"Host": f"127.0.0.1:{port}", **headers})
    return conn.getresponse().status


def test_rejects_cross_site_posts(server):
    assert _post_with(server, "/api/phrase", {"Origin": "https://evil.example.com"}) == 403
    assert _post_with(server, "/api/collect", {"Sec-Fetch-Site": "cross-site"}) == 403


def test_phrase_change_republishes(server, monkeypatch):
    import npsr_admin.server as srv_mod

    calls = []
    monkeypatch.setattr(srv_mod, "publish", lambda payload, cfg, push=True: calls.append(cfg.phrase))
    status, body = _req(server, "POST", "/api/phrase", {})
    assert status == 200 and calls and body["link"].endswith(calls[0])
