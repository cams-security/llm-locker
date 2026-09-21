import { fileURLToPath } from "node:url";
import path from "node:path";
import { config } from "dotenv";

// ESM has no built-in __dirname (unlike CommonJS) — recreate it from
// import.meta.url so the .env path below resolves regardless of cwd.
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Load the shared .env from the repo root (locker/.env), not a local copy —
// this compiles to mcp-server-node/dist/env.js, so '..' x2 reaches locker/.
//
// Why this is its own file: client.ts and crypto.ts both throw immediately
// if their required env vars are missing, at module *load* time. In ESM,
// static imports are hoisted and evaluated in declaration order before the
// importing module's own body runs — so putting this config() call inline
// in index.ts, even before its other import statements textually, would
// NOT run it first; index.ts's imports (including client.ts) all evaluate
// before any of index.ts's own code does. Making this a separate leaf
// module (no imports of its own) and importing it first from index.ts
// works, because sibling imports in the same file evaluate in order.
config({ path: path.join(__dirname, "..", "..", ".env") });
