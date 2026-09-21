import * as crypto from "./crypto.js";

const BASE_URL = process.env.LOCKER_API_URL || "http://127.0.0.1:8000";
const API_KEY = process.env.LOCKER_API_KEY;
if (!API_KEY) {
  throw new Error("LOCKER_API_KEY is not set — it must match the API server's key.");
}

// Built once at module load; every request reuses the same auth header.
// This is an authentication credential (proves the caller may use the
// API), not a confidentiality key — it's fine for the server to see this.
const HEADERS = { "X-API-Key": API_KEY, "Content-Type": "application/json" };

/**
 * A locker entry as returned to callers of this module — `content` here is
 * always plaintext, already decrypted by `saveMemory`/`listMemories` below.
 *
 * Over the wire and in the database, only `content` is ever ciphertext.
 * `type`, `tags`, and `created_at` are stored and transmitted as plaintext
 * deliberately, so the API can still filter by type/tag server-side — see
 * BACKLOG.md's End-to-end encryption section for the full tradeoff.
 */
export interface Memory {
  id: number;
  type: string;
  content: string;
  tags: string[];
  created_at: string;
}

/** Throws if `response` isn't a 2xx, with the response body in the message. */
async function assertOk(response: Response, label: string): Promise<void> {
  if (!response.ok) {
    throw new Error(`${label} failed: ${response.status} ${await response.text()}`);
  }
}

/**
 * Encrypts `content` client-side, then POSTs it to the API. The server and
 * database never receive or store plaintext — only the ciphertext produced
 * by `crypto.encrypt`. Returns the saved record with `content` restored to
 * the plaintext we already have, rather than decrypting our own
 * just-encrypted ciphertext straight back.
 */
export async function saveMemory(
  content: string,
  type: string = "memory",
  tags: string[] = [],
): Promise<Memory> {
  const response = await fetch(`${BASE_URL}/memories`, {
    method: "POST",
    headers: HEADERS,
    body: JSON.stringify({ content: crypto.encrypt(content), type, tags }),
  });
  await assertOk(response, "save_memory");
  const memory = (await response.json()) as Memory;
  memory.content = content;
  return memory;
}

/**
 * Fetches entries from the API — optionally filtered by `type`, or by a
 * single `tag` (exact match, applied server-side) — and decrypts each
 * entry's `content` here, client-side, before returning. The API itself
 * never decrypts anything; it only ever stores and returns opaque
 * ciphertext.
 */
export async function listMemories(type?: string, tag?: string): Promise<Memory[]> {
  const params = new URLSearchParams();
  if (type) params.set("type", type);
  if (tag) params.set("tag", tag);
  const response = await fetch(`${BASE_URL}/memories?${params}`, { headers: HEADERS });
  await assertOk(response, "list_memories");
  const memories = (await response.json()) as Memory[];
  for (const memory of memories) {
    memory.content = crypto.decrypt(memory.content);
  }
  return memories;
}
