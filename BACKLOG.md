# Backlog

Things to do before this is a tool other people can actually rely on, not
just a local prototype. Roughly ordered by priority within each section.

This is being built as a **service we host and operate for other people**,
not a repo we hand off for self-hosting. That changes the bar: security,
account isolation, and operational reliability aren't optional polish —
they're the actual product, since users are trusting us with their data
rather than controlling their own deployment.

Security and privacy are treated as a prerequisite for calling this
"usable by others," not a nice-to-have polish pass — the **Security &
privacy** section below should be considered blocking, ahead of feature
work like retrieval quality.

**Chosen threat model: security comparable to Signal, meaning true
end-to-end encryption — we, the operator, must not be able to read memory
content, not merely "encrypted at rest with a key we control."** That's a
stronger and different guarantee than server-side encryption, and it has
real consequences for other things in this backlog — see the dedicated
section below.

## End-to-end encryption (the actual security model)

This supersedes the earlier "application-level encryption with a key from
Key Vault" idea — a Key-Vault-held key is still an *operator*-held key,
which doesn't meet the bar. The encryption key must never reach the server.

- [x] **Encrypt/decrypt happens client-side, not in `api.py`.** Scaffolded
      in `crypto.py` (AES-256-GCM via `cryptography`, random nonce per
      call — never hand-rolled crypto) and wired into `client.py`:
      `save_memory` encrypts `content` before the HTTP call,
      `list_memories` decrypts after the response arrives. `api.py` and
      the database never hold the key and never see plaintext — verified
      by reading the raw SQLite row directly. `mcp_server.py` needed no
      changes since it calls through `client.py`, which is the actual
      encryption boundary.
- [ ] **Real key generation/management.** `crypto.py` currently reads a
      single static key from a `LOCKER_ENCRYPTION_KEY` env var — this is a
      placeholder that proves the server never sees plaintext, *not* the
      finished key-management story. Still needed: proper client-side key
      generation, the DEK/KEK split, and everything else in the items
      below.
- [ ] **The LLM itself still sees plaintext — this is an accepted,
      unavoidable boundary, not a gap to close.** Encryption happens in
      the tool handler (`client.py`), not in the model, because the model
      has to see memory content to decide what to write or use what it
      reads back. That means whatever inference provider is running the
      model (e.g. Anthropic, OpenAI) necessarily processes plaintext too.
      This gives a real guarantee — our server and anyone who breaches it
      never sees plaintext — but it is not the same as Signal's guarantee
      of no intermediary ever understanding the message. Worth stating
      explicitly wherever this security model is described to users, so
      "Signal-comparable" isn't read as a stronger claim than it is.
- [ ] **Rethink forward secrecy for a persistent store.** Signal's Double
      Ratchet rotates keys per-message and intentionally makes old
      messages undecryptable after the fact — that's the wrong model for
      us, since memories need to stay decryptable indefinitely rather than
      self-destruct. Use a stable per-tenant Data Encryption Key (DEK)
      wrapped by a user-controlled Key Encryption Key (KEK); rotate by
      re-wrapping the DEK under a new KEK, not by ratcheting per record.
- [ ] **Key backup / recovery flow.** The biggest risk to "ease of use"
      here: if the KEK only ever lives on one device and that device is
      lost, every memory becomes permanently unrecoverable — by design,
      since we can't recover it either. Needs a deliberate recovery
      mechanism (e.g. a one-time-shown recovery phrase, BIP39-style, that
      re-derives the KEK) before this goes anywhere near a real user.
- [ ] **Multi-device / multi-agent key distribution.** The writer-LLM and
      reader-LLM need the same key. Simplest workable model: one key per
      user/tenant, exported from the first device and imported on later
      ones via the recovery phrase above — not full pairwise Signal-style
      device linking (X3DH-equivalent key agreement between arbitrary
      agents), which is disproportionate complexity for what's really one
      identity accessing its own memories from multiple places.

### Consequences of E2EE for existing plans

Choosing true E2EE isn't free — it changes or blocks several things
already in this backlog. Flagging these now so they're deliberate
decisions later, not surprises:

- [ ] **Server-side tag/type filtering breaks or must move client-side.**
      `GET /memories?tag=` currently filters in SQL. If tags are encrypted
      too (matching the E2EE bar, not just `content`), filtering can only
      happen after client-side decryption. If tags stay plaintext instead
      so server-side filtering keeps working, that's a deliberate metadata
      exception to decide on explicitly, not an oversight — see the
      tag-matching bug in Correctness / storage below either way.
- [ ] **Semantic search (Retrieval quality section) is blocked as
      originally scoped.** Generating embeddings server-side requires
      plaintext content, which the server will never have under this
      model. Either drop server-side semantic search, or move embedding
      generation client-side and accept that similarity search can only
      run over data the client has already fetched and decrypted.
- [ ] **Support/debugging on user data is no longer possible, by design.**
      The support channel in "Operating this responsibly" can help with
      account/access issues but can never inspect a user's actual memory
      content — that's a feature of this security model, not a gap.
- [ ] **The Key Vault / CMK plan changes scope.** Key Vault still matters
      for API-key secrets, TLS certs, and other infra-level concerns — it
      just no longer holds the thing that decrypts memory content, because
      that key never reaches the server at all.

## Security & privacy (blocking)

- [ ] **Encrypt data at rest as defense in depth.** Even though content is
      already E2E-encrypted client-side, the ciphertext blob itself should
      still sit on encrypted storage — this is a second layer, not the
      primary guarantee.
      - SQLite (current state) has no native at-rest encryption — this is
        another reason the Postgres migration below is a blocker, not a
        nice-to-have.
      - Once on Azure Database for PostgreSQL Flexible Server, enable
        encryption at rest (Azure-managed key is fine here, since it's
        only protecting already-encrypted ciphertext, not the real secret).
- [ ] **Enforce encryption in transit.** HTTPS only, reject plaintext HTTP,
      enable HSTS. Azure App Service provides TLS termination by default —
      needs to actually be enforced, not just available.
- [ ] **Per-caller API keys**, not one shared static key. At minimum,
      separate read keys from write keys so a reader-LLM can't also write.
- [x] **Remove the hardcoded dev key fallback.** `auth.py`/`client.py` now
      raise at startup if `LOCKER_API_KEY` isn't set, instead of silently
      falling back to `dev-secret-key-change-me`. Done ahead of making the
      repo public — a known default credential documented in a public
      README would have been a real, working backdoor, not a hypothetical.
- [ ] **Secrets via Azure Key Vault**, not environment defaults baked into
      code.
- [ ] **Rate limiting / abuse protection** on the write endpoint.
- [ ] **Data minimization in logs.** Don't log request bodies or memory
      content in server/access logs — logs are an easy way to leak
      "encrypted at rest" data in plaintext by accident.
- [ ] **Access audit trail.** Record which key read/wrote which memory
      (metadata only, not content) so unauthorized access is detectable.
- [ ] **Real deletion + retention policy.** Ties to the update/delete
      endpoint item below — "delete" needs to actually remove the data, and
      we should decide on a retention/expiry policy before this holds real
      user data (GDPR-style right-to-delete territory once there are real
      users).

## Correctness / storage

- [ ] **Move off SQLite to Postgres.** SQLite's file locking doesn't hold up
      under concurrent writes, and gets worse on network-backed filesystems
      like Azure App Service's `/home` share. Azure Database for PostgreSQL
      Flexible Server is the natural target — `LOCKER_DB_URL` already makes
      this a config change, not a rewrite. Also a prerequisite for the
      at-rest encryption item above.
- [x] **Fix tag matching.** `tags` is now a real JSON list column
      (`models.py`), filtered by exact Python-side membership rather than
      SQL `LIKE` — `tag=cat` no longer matches `concatenate`. Covered by
      `test_tag_filter_is_exact_not_substring`. Filtering happens in
      application code rather than SQL because SQLite has no reliable JSON
      containment operator (unlike Postgres's `@>`); revisit once on
      Postgres if the personal-use row counts stop making that fine.
- [ ] **Add pagination** to `GET /memories` — it currently returns every row
      unbounded, which won't scale past a small number of memories.
- [ ] **Add update/delete endpoints.** Right now memories can only be
      created and read, never corrected or removed.
- [ ] **Add a size limit on `content`.** Nothing currently stops an
      unbounded write.

## Multi-tenancy

- [ ] **Add an owner/namespace field.** There's currently one global table —
      fine for a single person's agents, not fine the moment two people
      share a deployment and shouldn't see each other's memories. This is
      as much a privacy control as a feature: without it, tenant isolation
      doesn't exist regardless of how well-encrypted the data is.
- [ ] **Real accounts, not just keys.** A hosted multi-user service needs
      actual sign-up (email or OAuth) that owns a tenant, issues/revokes
      keys under it, and is the thing the owner/namespace field above
      actually references — an API key alone isn't a identity, it's a
      credential.

## Onboarding & self-service

The whole point of hosting this ourselves is that a user should never need
to touch Azure, a CLI, or a config file.

- [x] **Local/personal-use setup, done.** `setup.py` generates `.env` with
      both keys on first run (idempotent), `start.sh` is a one-command
      start, and `api.py`/`mcp_server.py` load `.env` automatically. Claude
      Code (`.mcp.json`) and VS Code Copilot Chat (`.vscode/mcp.json`)
      both share that `.env` with zero manual exports. Claude Desktop
      turned out to be a real exception, not just more config: current
      versions don't read `mcpServers` from `claude_desktop_config.json`
      for local servers at all anymore (confirmed via
      `LocalMcpServerManager` in its own logs) — they require a packaged
      `.mcpb` extension instead, built via `desktop-extension/build.sh`,
      with the two keys pasted into its install prompt by hand since the
      sandboxed extension can't see `.env`. All three (Claude Code, VS
      Code Copilot Chat, Claude Desktop) confirmed working live, not just
      programmatically. All of this is single-machine,
      single-user convenience only — it does nothing for the actual
      hosted-onboarding items below, which require a server other people
      can sign up to.
- [x] **Repo reorganized: all Python (`api.py`, `client.py`, `mcp_server.py`,
      etc.) now lives in `server/`**, alongside a new `mcp-server-node/` —
      a wire-compatible Node/TypeScript reimplementation of the MCP client
      (verified interoperable: either client can decrypt what the other
      wrote), intended as the primary distributed client going forward
      (Homebrew, etc.) while `server/` becomes purely the hosted API.
      `.env` stays at the repo root, read via an explicit resolved path by
      everything that needs it, not cwd-based discovery — this is what
      makes it keep working regardless of which subfolder something runs
      from.
- [ ] **Sign-up flow** — get a working key in under a minute, no manual
      provisioning on our end per user.
- [ ] **Self-service key dashboard** — create, view, and revoke keys;
      separate read/write keys per the Security section above.
- [ ] **One-line MCP install pointed at the hosted API by default** —
      `mcp_server.py`/`client.py` currently default `LOCKER_API_URL` to
      `http://127.0.0.1:8000`; packaged/distributed versions should default
      to the hosted URL so a user only has to supply their key.
- [ ] **Custom domain** (not `*.azurewebsites.net`) — cosmetic but also
      needed for a credible TLS/cert story on a real product.
- [ ] **Per-tenant rate limits/quotas**, not just global rate limiting —
      one noisy tenant shouldn't be able to degrade service for everyone
      else sharing the deployment.

## Agent collaboration / shared channels (proposed, not scoped)

Idea: a shared room/channel multiple agents can post to and read from, for
coordination — not just one-owner private memory. Worth designing as a
generalization of a pattern that's already showing up twice:

- **Durable private memory** (built) — one owner, persists until deleted.
- **One-time handoff** (proposed earlier, not built) — one-to-one,
  consumed and gone after first read.
- **Shared room** (this) — many-to-many, persistent, not consumed.

These are the same underlying primitive (an encrypted record with a
lifecycle and a visibility scope) with different settings, not three
unrelated features — worth keeping that in mind so this doesn't turn into
three separate subsystems that drift apart.

- [ ] **Security: this is a prompt-injection vector between your own
      agents, and needs to be treated as one.** If Agent A can post
      arbitrary content to a room Agent B later reads and acts on, that's
      the same risk class as an agent reading untrusted web content —
      except it's easy to overlook here because it's "your own system."
      Access control alone doesn't solve this; content from a shared room
      needs to be treated as untrusted input by whatever agent consumes
      it, the same way you'd treat scraped web content, not as trusted
      system state.
- [ ] **Poll, not push.** Chat rooms conventionally imply live delivery,
      but most agents aren't long-running listeners — they run, do a
      task, exit. A `since` parameter (messages after a given id/timestamp)
      fits how agents actually operate much better than websockets/push,
      at least as a starting point.
- [ ] **Open question: reuse the existing schema or a new primitive?**
      Could stretch `type`/`tags` to mean `type: "chat"`,
      `tags: "room:project-x"` — cheap, but a stretch. A proper
      `room`/`channel` concept is more correct but is new modeling work.
      Decide once there's a concrete use case driving it, not speculatively.
- [ ] **Key distribution gets harder, not just bigger.** The single-key
      model in the E2EE section assumes one owner. A room read by multiple
      distinct agents needs those agents to share a room-scoped key (or
      accept per-room keys), which is the "multi-party key agreement"
      complexity already flagged as disproportionate for the one-owner
      case — a shared room is exactly the scenario where it stops being
      avoidable, so this may force the key-distribution design sooner than
      the rest of the roadmap would otherwise require.

## Hosting / ops

Target topology (~$30–50/mo, within the $150/mo Azure credit). Supersedes
the free-tier `az webapp up` prototype from earlier — F1 doesn't support
the VNet integration this plan depends on.

**Updated since E2EE landed**: `crypto.py` encrypts memory content
client-side, so the server and database only ever handle ciphertext,
regardless of where the server runs. `LOCKER_ENCRYPTION_KEY` — the actual
secret — lives wherever `mcp_server.py` runs (your local machine), not on
Azure at all. That removes the need for a customer-managed key on
Postgres (it'd only be protecting already-opaque data) and shrinks Key
Vault's job to just `LOCKER_API_KEY` and TLS certs.

- [ ] **Resource Group** — `rg-llm-locker`, everything scoped together.
- [ ] **App Service (Linux, Python), Basic (B1) tier or higher** — hosts the
      FastAPI app. Needs to be at least B1 since F1 can't do VNet
      integration.
- [ ] **Azure Database for PostgreSQL Flexible Server** (Burstable `B1ms`
      to start) — replaces SQLite (whose file locking doesn't hold up on
      App Service's SMB-backed storage). Default Azure-managed encryption
      at rest is sufficient — see note above.
- [ ] **Azure Key Vault** — holds `LOCKER_API_KEY` and TLS certs. Does
      *not* hold `LOCKER_ENCRYPTION_KEY` — that never leaves the client.
- [ ] **System-assigned Managed Identity** on the App Service — lets it
      authenticate to Key Vault and Postgres with no stored credentials;
      required for Key Vault references in App Settings to work.
- [ ] **VNet integration + private endpoints** for Postgres and Key Vault —
      keeps the database and the API key off the public internet, reachable
      only from the app.
- [ ] **Application Insights** — request counts/error rates, without
      capturing memory content (ties to the log data-minimization item
      above).
- [ ] Wire `LOCKER_API_KEY`/`LOCKER_DB_URL` as Key Vault references in App
      Settings instead of local env vars.
- [ ] Update `LOCKER_API_URL` in every client config (`.env`,
      `.vscode/mcp.json`, `.mcp.json`, the Claude Desktop extension's
      `user_config`) to point at the hosted URL instead of `localhost`.
- [ ] CI: run `pytest` on every PR (GitHub Actions).
- [ ] CD: auto-deploy `main` to Azure on merge.

## Operating this responsibly for other people

Running this ourselves means we own the consequences when it breaks or
someone's data is at risk — this section is what that responsibility
actually requires, beyond just standing up the resources.

- [ ] **Backups + tested restore.** Postgres point-in-time restore
      configured *and* actually tested — an untested backup isn't a backup.
- [ ] **Uptime monitoring + alerting** on top of Application Insights above,
      so an outage is caught by us before a user reports it.
- [ ] **Status page** — somewhere users can check "is it down" without
      opening a support request.
- [ ] **Support / account-deletion channel** — a real way for a user to
      reach us, including to exercise the right-to-delete from the
      Security & privacy section. Per the E2EE section above, support can
      act on a user's data (delete it, restore a backup) but can never
      read its content — worth setting that expectation with users
      up front.
- [ ] **Terms of Service + Privacy Policy.** Once real people's data is
      being stored on infrastructure we control, this stops being
      optional — needs to exist before onboarding anyone beyond us.
- [ ] **Abuse / acceptable-use policy.** An open write endpoint for
      arbitrary content is a place people can try to store things they
      shouldn't; decide what's disallowed and how it's enforced before
      opening this up broadly.

## Retrieval quality

- [ ] Exact type/tag filtering is fine for a prototype, but real usefulness
      probably needs semantic search eventually. **Blocked/reshaped by the
      E2EE decision above** — server-side embeddings need plaintext
      content the server won't have; needs a client-side design instead of
      the originally assumed server-side one.

## Client / SDK polish

- [ ] Add retries/timeouts to `client.py` and `mcp_server.py` — right now a
      slow or down server just hangs or throws.
- [ ] Package `client.py`/`mcp_server.py` as an installable package if other
      projects are going to depend on them, per the earlier packaging
      discussion.
