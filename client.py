import os
from typing import List, Optional

import httpx

import crypto

BASE_URL = os.environ.get("LOCKER_API_URL", "http://127.0.0.1:8000")
API_KEY = os.environ.get("LOCKER_API_KEY")
if not API_KEY:
    raise RuntimeError("LOCKER_API_KEY is not set — it must match the API server's key.")

_HEADERS = {"X-API-Key": API_KEY}


def save_memory(content: str, type: str = "memory", tags: Optional[str] = None) -> dict:
    response = httpx.post(
        f"{BASE_URL}/memories",
        json={"content": crypto.encrypt(content), "type": type, "tags": tags},
        headers=_HEADERS,
    )
    response.raise_for_status()
    memory = response.json()
    memory["content"] = content
    return memory


def list_memories(type: Optional[str] = None, tag: Optional[str] = None) -> List[dict]:
    params = {k: v for k, v in {"type": type, "tag": tag}.items() if v is not None}
    response = httpx.get(f"{BASE_URL}/memories", params=params, headers=_HEADERS)
    response.raise_for_status()
    memories = response.json()
    for memory in memories:
        memory["content"] = crypto.decrypt(memory["content"])
    return memories
