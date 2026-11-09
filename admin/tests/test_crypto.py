import json
import re
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidTag

from npsr_admin.crypto import decrypt_json, encrypt_json, new_salt
from npsr_admin.phrase import WORDS, new_phrase

FIXTURES = Path(__file__).resolve().parents[2] / "web" / "tests" / "fixtures"
PHRASE = "arbuz-volk-luna-sad-42"
PLAIN = {"hello": "мир", "n": [1, 2.5]}


def test_round_trip():
    env = encrypt_json(PLAIN, PHRASE, new_salt())
    assert env["v"] == 1 and env["alg"] == "AES-GCM" and env["kdf"] == "PBKDF2-SHA256" and env["iter"] == 250_000
    assert decrypt_json(env, PHRASE) == PLAIN


def test_wrong_phrase_fails():
    env = encrypt_json(PLAIN, PHRASE, new_salt())
    with pytest.raises(InvalidTag):
        decrypt_json(env, "wrong-phrase")


def test_phrase_shape():
    p = new_phrase()
    assert re.fullmatch(r"[a-z]+(-[a-z]+){3}-\d{2}", p)
    assert len(WORDS) >= 300


def test_committed_browser_fixture_matches_python():
    """web/tests/fixtures/envelope.json (committed, read by the browser test) decrypts in Python."""
    data = json.loads((FIXTURES / "envelope.json").read_text(encoding="utf-8"))
    assert decrypt_json(data["env"], data["phrase"]) == data["plain"]


def test_decrypts_ts_envelope():
    path = FIXTURES / "generated" / "envelope_ts.json"
    if not path.exists():
        pytest.skip("run `npm test` in web/ first to produce the TS envelope")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert decrypt_json(data["env"], data["phrase"]) == data["plain"]
