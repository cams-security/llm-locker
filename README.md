# llm-locker

A 'locker' for LLM memories/tools/etc

An API where one LLM can write memories, tools, or other notes, and another
LLM (or the same one, later) can read them back — gated behind an API key.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
```

This creates `.venv` and installs all dependencies from `pyproject.toml`.

## Running the API

```bash
uv run uvicorn api:app --reload --port 8000
```

- `--reload` restarts the server automatically when you edit the code.
- Browse to `http://127.0.0.1:8000/docs` for interactive API docs.
- Requires a `LOCKER_API_KEY` env var (the server refuses to start without
  one — there is no default). Generate one with:
  ```bash
  export LOCKER_API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
  ```
  All `/memories` endpoints require this key in an `X-API-Key` header.

Data is stored in a local SQLite file (`memories.db` by default, override
with `LOCKER_DB_URL`).

## Running the tests

```bash
uv run pytest -v
```

Runs both `test_api.py` (the HTTP API) and `test_crypto.py` (the
encryption module).

## Using the client / MCP server

`client.py` provides `save_memory()` / `list_memories()` for calling the API
directly. `mcp_server.py` wraps those same functions as MCP tools so an
MCP-aware client (e.g. VS Code Copilot Chat in Agent Mode) can call them:

```bash
uv run python mcp_server.py
```

Both read `LOCKER_API_URL` (default `http://127.0.0.1:8000`) and
`LOCKER_API_KEY` from the environment, so they need to match whatever the
API server is running with, and the API server needs to already be running
for either to work.

**Memory content is end-to-end encrypted by `client.py` before it's sent**
— the server and database only ever see ciphertext (see BACKLOG.md's
End-to-end encryption section for the full design and its current
limitations). This requires a `LOCKER_ENCRYPTION_KEY` env var, a
base64-encoded 32-byte key:

```bash
export LOCKER_ENCRYPTION_KEY=$(python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())")
```

Whoever writes a memory and whoever reads it back need the *same* key —
there's no key-sharing mechanism yet beyond setting the same env var
yourself. This only protects `content`; `type` and `tags` remain plaintext
on the server so filtering still works. Note this protection only applies
when going through `client.py`/`mcp_server.py` — hitting the API directly
(`curl`, the `/docs` page) stores whatever you send it, encrypted or not,
since the API server has no encryption logic of its own.

## Roadmap

See [BACKLOG.md](BACKLOG.md) for what's left before this is usable by
people other than us.
