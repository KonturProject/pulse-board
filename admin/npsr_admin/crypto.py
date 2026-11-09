"""AES-GCM 256 with a PBKDF2-SHA-256 key from the access phrase — byte-compatible with web/src/crypto.ts.

Envelope: {v: 1, alg: "AES-GCM", kdf: "PBKDF2-SHA256", iter, salt, iv, ciphertext} (base64).
"""

import base64
import json
import os
from functools import lru_cache

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

KDF_ITERATIONS = 250_000


def new_salt() -> bytes:
    return os.urandom(16)


@lru_cache(maxsize=8)
def _key(phrase: str, salt: bytes, iterations: int) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    return kdf.derive(phrase.encode("utf-8"))


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def encrypt_json(value: object, phrase: str, salt: bytes, iterations: int = KDF_ITERATIONS) -> dict:
    iv = os.urandom(12)
    plain = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    cipher = AESGCM(_key(phrase, salt, iterations)).encrypt(iv, plain, None)
    return {"v": 1, "alg": "AES-GCM", "kdf": "PBKDF2-SHA256", "iter": iterations,
            "salt": _b64(salt), "iv": _b64(iv), "ciphertext": _b64(cipher)}


def decrypt_json(env: dict, phrase: str) -> object:
    """Raises cryptography.exceptions.InvalidTag on a wrong phrase or a damaged file."""
    key = _key(phrase, base64.b64decode(env["salt"]), int(env["iter"]))
    plain = AESGCM(key).decrypt(base64.b64decode(env["iv"]), base64.b64decode(env["ciphertext"]), None)
    return json.loads(plain.decode("utf-8"))
