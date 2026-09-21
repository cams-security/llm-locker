import base64
import os
import secrets

os.environ.setdefault(
    "LOCKER_ENCRYPTION_KEY", base64.b64encode(secrets.token_bytes(32)).decode()
)

import crypto


def test_round_trip():
    assert crypto.decrypt(crypto.encrypt("hello locker")) == "hello locker"


def test_ciphertext_does_not_contain_plaintext():
    ciphertext = crypto.encrypt("a very secret memory")
    assert "a very secret memory" not in ciphertext


def test_encryption_is_nondeterministic():
    first = crypto.encrypt("same plaintext")
    second = crypto.encrypt("same plaintext")
    assert first != second


def test_missing_key_raises():
    saved = os.environ.pop("LOCKER_ENCRYPTION_KEY")
    try:
        try:
            crypto.encrypt("test")
            assert False, "expected RuntimeError"
        except RuntimeError:
            pass
    finally:
        os.environ["LOCKER_ENCRYPTION_KEY"] = saved
