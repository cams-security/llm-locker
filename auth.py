import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY = os.environ.get("LOCKER_API_KEY", "dev-secret-key-change-me")

_api_key_header = APIKeyHeader(name="X-API-Key")


def require_api_key(provided_key: str = Security(_api_key_header)) -> None:
    if not secrets.compare_digest(provided_key, API_KEY):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
