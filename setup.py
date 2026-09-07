import base64
import secrets
from pathlib import Path

ENV_PATH = Path(__file__).parent / ".env"


def main() -> None:
    existing = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, _, value = line.partition("=")
                existing[key.strip()] = value.strip()

    changed = False
    if "LOCKER_API_KEY" not in existing:
        existing["LOCKER_API_KEY"] = secrets.token_urlsafe(32)
        changed = True
    if "LOCKER_ENCRYPTION_KEY" not in existing:
        existing["LOCKER_ENCRYPTION_KEY"] = base64.b64encode(secrets.token_bytes(32)).decode()
        changed = True

    if changed:
        ENV_PATH.write_text("\n".join(f"{key}={value}" for key, value in existing.items()) + "\n")
        print(f"Wrote {ENV_PATH}")
    else:
        print(f"{ENV_PATH} already has both keys — nothing to do.")


if __name__ == "__main__":
    main()
