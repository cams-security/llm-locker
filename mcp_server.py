from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()

from mcp.server.mcpserver import MCPServer

import client

mcp = MCPServer("locker")


@mcp.tool()
def save_memory(content: str, type: str = "memory", tags: Optional[str] = None) -> dict:
    """Save a memory, tool description, or note to the locker."""
    return client.save_memory(content=content, type=type, tags=tags)


@mcp.tool()
def list_memories(type: Optional[str] = None, tag: Optional[str] = None) -> List[dict]:
    """List memories from the locker, optionally filtered by type or tag."""
    return client.list_memories(type=type, tag=tag)


if __name__ == "__main__":
    mcp.run()
