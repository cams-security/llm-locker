# server/

Everything Python-related for llm-locker lives here.

## Two different things live in this folder

**The REST API** (`api.py`, `auth.py`, `db.py`, `models.py`) — active,
deployed. This is the hosted service; the Azure App Service it runs on is
explicitly configured for `PYTHON|3.12`. Not going anywhere.

**The Python MCP client** (`client.py`, `crypto.py`, `mcp_server.py`) —
**deprecated.** [`mcp-server-node/`](../mcp-server-node/) at the repo root
is a wire-compatible replacement (verified interoperable — either
implementation can decrypt what the other wrote) and is the one going
forward, mainly for distribution reasons (Homebrew, no Python/`uv`
dependency for end users — see the conversation history / commit log for
the full reasoning). These three files are being kept in place for
reference and as a fallback, not actively developed further. New MCP
client work should happen in `mcp-server-node/`.

## Running the API server

See the top-level [README.md](../README.md) — setup, running locally,
running tests, and deployment are all documented there.
