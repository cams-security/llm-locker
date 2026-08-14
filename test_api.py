import os

os.environ.setdefault("LOCKER_API_KEY", "dev-secret-key-change-me")

from fastapi.testclient import TestClient

from api import app
from auth import API_KEY
from db import create_db_and_tables

create_db_and_tables()

client = TestClient(app)
HEADERS = {"X-API-Key": API_KEY}


def test_health():
    response = client.get("/")
    assert response.status_code == 200


def test_requires_api_key():
    response = client.get("/memories")
    assert response.status_code == 401


def test_rejects_wrong_api_key():
    response = client.get("/memories", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401


def test_write_and_read_memory():
    created = client.post(
        "/memories",
        json={"type": "memory", "content": "test content", "tags": "test"},
        headers=HEADERS,
    )
    assert created.status_code == 200
    memory_id = created.json()["id"]

    listed = client.get("/memories", headers=HEADERS)
    assert listed.status_code == 200
    assert any(m["id"] == memory_id for m in listed.json())

    fetched = client.get(f"/memories/{memory_id}", headers=HEADERS)
    assert fetched.status_code == 200
    assert fetched.json()["content"] == "test content"
