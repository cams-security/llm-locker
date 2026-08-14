import os
from typing import List, Optional

import httpx

BASE_URL = os.environ.get("LOCKER_API_URL", "http://127.0.0.1:8000")
API_KEY = os.environ.get("LOCKER_API_KEY", "dev-secret-key-change-me")

_HEADERS = {"X-API-Key": API_KEY}


def save_memory(content: str, type: str = "memory", tags: Optional[str] = None) -> dict:
    response = httpx.post(
        f"{BASE_URL}/memories",
        json={"content": content, "type": type, "tags": tags},
        headers=_HEADERS,
    )
    response.raise_for_status()
    return response.json()


def list_memories(type: Optional[str] = None, tag: Optional[str] = None) -> List[dict]:
    params = {k: v for k, v in {"type": type, "tag": tag}.items() if v is not None}
    response = httpx.get(f"{BASE_URL}/memories", params=params, headers=_HEADERS)
    response.raise_for_status()
    return response.json()
