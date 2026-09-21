# DEPRECATED: mcp-server-node/ (repo root) is the wire-compatible
# replacement and the one going forward. This file is kept for reference
# and as a fallback, not under active development. See server/README.md.

from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

# See api.py for why this is an explicit path rather than a bare load_dotenv().
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from mcp.server.mcpserver import MCPServer

import client

mcp = MCPServer("locker")


@mcp.tool()
def save_memory(content: str, type: str = "memory", tags: Optional[List[str]] = None) -> dict:
    """Save an encrypted entry to the locker.

    type must be one of:
      - "memory": a fact worth recalling later (user preferences, project details, etc.)
      - "tool": reference info about an external tool/API (not this locker's own tools —
        those are already described by this MCP server's tool definitions)
      - "note": anything else worth keeping that doesn't fit the above

    tags is a list of lowercase keywords, e.g. ["preferences", "denver"]. Reuse
    existing tags where they fit — list_memories() with no arguments returns
    everything, so check what's already there before inventing new ones.
    """
    return client.save_memory(content=content, type=type, tags=tags)


@mcp.tool()
def list_memories(type: Optional[str] = None, tag: Optional[str] = None) -> List[dict]:
    """List entries from the locker, optionally filtered by type ("memory"/"tool"/"note")
    or by a single tag (exact match against each entry's tags list)."""
    return client.list_memories(type=type, tag=tag)


if __name__ == "__main__":
    mcp.run()
