# llm-locker

A 'locker' for LLM memories/tools/etc

An API where one LLM can write memories, tools, or other notes, and another
LLM (or the same one, later) can read them back — gated behind an API key.

## Layout

- **`server/`** — the Python REST API (`api.py`) plus the original Python
  MCP client (`client.py`/`mcp_server.py`). Everything Python-related lives
  here; see below for why.
- **`mcp-server-node/`** — a Node/TypeScript MCP client, wire-compatible
  with the Python one (interoperable ciphertext — either can read what the
  other wrote). Intended as the primary distributed client going forward
  (Homebrew, etc.); see its own directory for details.
- **`desktop-extension/`** — packages `server/mcp_server.py` as a `.mcpb`
  bundle for Claude Desktop.
- **`infra/`** — Bicep templates for hosting `server/` on Azure.
- **`.env`** at the repo root — shared secrets, read by everything above
  regardless of which subfolder it runs from. Never commit it.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
cd server
uv sync
```

This creates `server/.venv` and installs all dependencies from
`server/pyproject.toml`.

## Running the API

```bash
cd server
./start.sh
```

First run creates a `.env` file **at the repo root** (one level up from
`server/`) with a generated `LOCKER_API_KEY` and `LOCKER_ENCRYPTION_KEY`
(via `setup.py` — safe to re-run, it won't overwrite keys that already
exist), then starts the server with `--reload`. Every piece (`api.py`,
`client.py`/`mcp_server.py`, and `mcp-server-node`) loads that same shared
`.env` automatically via an explicit path — not by relying on the current
directory — so nothing needs to be manually exported regardless of where
it's run from. `.env` is already covered by `.gitignore` — never commit it.

- Browse to `http://127.0.0.1:8000/docs` for interactive API docs.
- All `/memories` endpoints require the `LOCKER_API_KEY` value in an
  `X-API-Key` header.

Data is stored in a local SQLite file (`server/memories.db` by default,
override with `LOCKER_DB_URL`).

## Running the tests

```bash
cd server
uv run pytest -v
```

Runs both `test_api.py` (the HTTP API) and `test_crypto.py` (the
encryption module).

## Using the client / MCP server

`mcp-server-node/` (repo root) is the actively-developed MCP client —
wire-compatible AES-256-GCM encryption, same two tools (`save_memory`,
`list_memories`). See its own directory for setup.

`server/client.py`/`server/mcp_server.py` are the original Python
implementation of the same two tools. **Deprecated** — kept for reference
and as a fallback, not under active development; see
[`server/README.md`](server/README.md) for why. Still functional if you
need it: it also loads the shared `.env` automatically, so as long as the
API server has been started at least once (to generate `.env` via
`setup.py`), no manual environment setup is needed.

**The API server must already be running** (`cd server && ./start.sh`) for
either client to work.

Already registered as an MCP server for:
- **VS Code Copilot Chat** (Agent Mode) — `.vscode/mcp.json`
- **Claude Code** — `.mcp.json` at the repo root (auto-discovered)
- **Claude Desktop** — as a packaged extension, see below

VS Code and Claude Code currently launch `server/mcp_server.py` (the
deprecated Python client) directly via `uv run --directory server` and
share `.env` automatically — no per-client key configuration. Switching
these to `mcp-server-node/` is a follow-up, not yet done.

### Claude Desktop (packaged as an MCPB extension)

Current versions of Claude Desktop don't read `mcpServers` out of
`claude_desktop_config.json` for locally-added servers anymore — they load
extensions packaged as `.mcpb` bundles instead (confirmed via
`~/Library/Logs/Claude/main.log`: `[LocalMcpServerManager]`). The bundle is
in `desktop-extension/`:

```bash
cd desktop-extension && ./build.sh
```

This copies `server/mcp_server.py`/`server/client.py`/`server/crypto.py`
into `desktop-extension/src/` (kept out of git — `build.sh` is the source
of truth, not the copies) and produces `llm-locker.mcpb`. In Claude
Desktop: **Settings → Extensions → Install Extension**, pick that file.
Unlike VS Code/Claude Code, this **does not** read `.env` automatically —
the extension's own sandboxed `uv` environment has no access to it. You'll
be prompted for `Locker API Key` and `Locker Encryption Key` during
install; copy those two values from the repo root's `.env` and paste them
in. Re-run `build.sh` and reinstall after changing anything in `server/`.

**Memory content is end-to-end encrypted by the client before it's sent**
— the server and database only ever see ciphertext (see BACKLOG.md's
End-to-end encryption section for the full design and its current
limitations). This only protects `content`; `type` and `tags` remain
plaintext on the server so filtering still works. Note this protection only
applies when going through a real client (`server/client.py`,
`server/mcp_server.py`, or `mcp-server-node`) — hitting the API directly
(`curl`, the `/docs` page) stores whatever you send it, encrypted or not,
since the API server has no encryption logic of its own.

The current `.env`-based key is still a single shared secret you're
trusting your local machine with — see BACKLOG.md for why this is a
placeholder, not the real key-management design.

## Roadmap

See [BACKLOG.md](BACKLOG.md) for what's left before this is usable by
people other than us.
