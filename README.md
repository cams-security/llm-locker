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
./start.sh
```

First run creates a `.env` file with a generated `LOCKER_API_KEY` and
`LOCKER_ENCRYPTION_KEY` (via `setup.py` — safe to re-run, it won't
overwrite keys that already exist), then starts the server with
`--reload`. Every piece (`api.py`, `client.py`/`mcp_server.py`) loads
`.env` automatically, so nothing needs to be manually exported. `.env` is
already covered by `.gitignore` — never commit it.

- Browse to `http://127.0.0.1:8000/docs` for interactive API docs.
- All `/memories` endpoints require the `LOCKER_API_KEY` value in an
  `X-API-Key` header.

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
MCP-aware client can call them — it also loads `.env` automatically, so as
long as the API server has been started at least once (to generate `.env`
via `setup.py`), no manual environment setup is needed.

**The API server must already be running** (`./start.sh`) for either to work.

Already registered as an MCP server for:
- **VS Code Copilot Chat** (Agent Mode) — `.vscode/mcp.json`
- **Claude Code** — `.mcp.json` at the repo root (auto-discovered)
- **Claude Desktop** — as a packaged extension, see below

VS Code and Claude Code both launch `mcp_server.py` directly via `uv run`
and share `.env` automatically — no per-client key configuration.

### Claude Desktop (packaged as an MCPB extension)

Current versions of Claude Desktop don't read `mcpServers` out of
`claude_desktop_config.json` for locally-added servers anymore — they load
extensions packaged as `.mcpb` bundles instead (confirmed via
`~/Library/Logs/Claude/main.log`: `[LocalMcpServerManager]`). The bundle is
in `desktop-extension/`:

```bash
cd desktop-extension && ./build.sh
```

This copies `mcp_server.py`/`client.py`/`crypto.py` into `desktop-extension/src/`
(kept out of git — `build.sh` is the source of truth, not the copies) and
produces `llm-locker.mcpb`. In Claude Desktop: **Settings → Extensions →
Install Extension**, pick that file. Unlike VS Code/Claude Code, this
**does not** read `.env` automatically — the extension's own sandboxed `uv`
environment has no access to it. You'll be prompted for `Locker API Key`
and `Locker Encryption Key` during install; copy those two values from
`locker/.env` and paste them in. Re-run `build.sh` and reinstall after
changing `mcp_server.py`/`client.py`/`crypto.py`.

**Memory content is end-to-end encrypted by `client.py` before it's sent**
— the server and database only ever see ciphertext (see BACKLOG.md's
End-to-end encryption section for the full design and its current
limitations). This only protects `content`; `type` and `tags` remain
plaintext on the server so filtering still works. Note this protection only
applies when going through `client.py`/`mcp_server.py` — hitting the API
directly (`curl`, the `/docs` page) stores whatever you send it, encrypted
or not, since the API server has no encryption logic of its own.

The current `.env`-based key is still a single shared secret you're
trusting your local machine with — see BACKLOG.md for why this is a
placeholder, not the real key-management design.

## Roadmap

See [BACKLOG.md](BACKLOG.md) for what's left before this is usable by
people other than us.
