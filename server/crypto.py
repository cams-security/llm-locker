# DEPRECATED: mcp-server-node/src/crypto.ts (repo root) is the
# wire-compatible replacement and the one going forward. This file is kept
# for reference and as a fallback, not under active development. See
# server/README.md.

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_NONCE_SIZE = 12


def _load_key() -> bytes:
    encoded = os.environ.get("LOCKER_ENCRYPTION_KEY")
    if not encoded:
        raise RuntimeError(
            "LOCKER_ENCRYPTION_KEY is not set. Generate one with:\n"
            '  python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"\n'
            "and keep it off the server. This is a placeholder for the DEK/KEK + "
            "recovery-phrase flow described in BACKLOG.md — a single static key is "
            "enough to prove the server never sees plaintext, not the finished "
            "key-management story."
        )
    key = base64.b64decode(encoded)
    if len(key) != 32:
        raise RuntimeError("LOCKER_ENCRYPTION_KEY must decode to 32 bytes (AES-256).")
    return key


def encrypt(plaintext: str) -> str:
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = AESGCM(_load_key()).encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt(encoded: str) -> str:
    raw = base64.b64decode(encoded)
    nonce, ciphertext = raw[:_NONCE_SIZE], raw[_NONCE_SIZE:]
    plaintext = AESGCM(_load_key()).decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")
