#!/usr/bin/env node
// MCP server entry point: registers the two tools an LLM can call
// (save_memory, list_memories) and serves them over stdio. "./env.js" must
// be the first import — see env.ts for why the ordering matters.
// The shebang above is what makes the compiled dist/index.js directly
// executable once installed (Homebrew, npm's `bin` linking, etc.) rather
// than needing `node dist/index.js` spelled out every time.
import "./env.js";
import { McpServer } from "@modelcontextprotocol/server";
import { StdioServerTransport } from "@modelcontextprotocol/server/stdio";
import * as z from "zod/v4";
import { listMemories, saveMemory } from "./client.js";

const server = new McpServer({ name: "locker", version: "1.0.0" });

// The `description` strings below are read by the calling LLM, not just by
// humans skimming this file — they're the tool's actual interface contract,
// which is why they spell out valid `type` values and tag conventions
// explicitly rather than leaving them for the model to guess at.
server.registerTool(
  "save_memory",
  {
    description: `Save an encrypted entry to the locker.

type must be one of:
  - "memory": a fact worth recalling later (user preferences, project details, etc.)
  - "tool": reference info about an external tool/API (not this locker's own tools —
    those are already described by this MCP server's tool definitions)
  - "note": anything else worth keeping that doesn't fit the above

tags is a list of lowercase keywords, e.g. ["preferences", "denver"]. Reuse
existing tags where they fit — list_memories() with no arguments returns
everything, so check what's already there before inventing new ones.`,
    inputSchema: z.object({
      content: z.string(),
      type: z.string().default("memory"),
      tags: z.array(z.string()).optional(),
    }),
  },
  async ({ content, type, tags }) => {
    const memory = await saveMemory(content, type, tags ?? []);
    // MCP tool results must be wrapped in a content-block array (the
    // protocol's format, not a choice made here) — a plain returned object
    // isn't valid on its own, unlike Python's mcp[cli], which handles this
    // wrapping for you.
    return { content: [{ type: "text", text: JSON.stringify(memory) }] };
  },
);

server.registerTool(
  "list_memories",
  {
    description:
      'List entries from the locker, optionally filtered by type ("memory"/"tool"/"note") ' +
      "or by a single tag (exact match against each entry's tags list).",
    inputSchema: z.object({
      type: z.string().optional(),
      tag: z.string().optional(),
    }),
  },
  async ({ type, tag }) => {
    const memories = await listMemories(type, tag);
    return { content: [{ type: "text", text: JSON.stringify(memories) }] };
  },
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main();
