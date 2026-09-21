# homebrew/

A Homebrew formula for `mcp-server-node`, packaging it as the
`llm-locker-mcp` command.

**Status: formula written and fully tested locally, not yet a published
tap.** Verified via a local Homebrew tap (`brew tap-new`) — real install,
real `brew test`, and a genuine encrypted `save_memory`/`list_memories`
round trip through the installed binary against a live API server. Not
yet installable by anyone else, because that requires a real public
`homebrew-llm-locker` repo (Homebrew's tap naming convention — `brew tap
cams-security/llm-locker` resolves to `cams-security/homebrew-llm-locker`)
for `Formula/llm-locker.rb` to actually live in. That's a new public
GitHub repo, a separate step from writing/testing the formula itself.

## Testing this formula locally

```bash
brew tap-new cams-security/llm-locker --no-git
cp Formula/llm-locker.rb "$(brew --repository cams-security/llm-locker)/Formula/"
brew install --build-from-source cams-security/llm-locker/llm-locker
brew test cams-security/llm-locker/llm-locker
```

## How it works

- `depends_on "node"` — Node itself isn't bundled, has to be present.
- The formula runs a normal local `npm install` + `npm run build` first
  (producing `dist/`), then Homebrew's standard global-style npm install
  (`std_npm_args`) into `libexec` — the latter passes `--ignore-scripts`,
  which deliberately skips the `build` npm lifecycle script, so it has to
  happen explicitly beforehand or `dist/index.js` never gets created.
- `mcp-server-node/src/index.ts` has a `#!/usr/bin/env node` shebang
  (survives `tsc` compilation) and `package.json` declares a `bin` entry,
  which is what makes `dist/index.js` linkable as a standalone
  `llm-locker-mcp` command rather than needing `node dist/index.js`
  spelled out.
