# Append-only JSONL audit log for order-mutating actions

Because the adapter executes real trades on behalf of LLM agent clients (per ADR-0001), the user needs a reliable, machine-parseable record of "what did the agent do" they can review later. The adapter writes a JSON-Lines (`jsonl`) file at a platform-aware user data path (default `~/.local/share/ibkr-mcp/audit.jsonl`, override via `IBKR_AUDIT_LOG_PATH`, file mode `0600`). One line is appended for each order-mutating call — `preview_*`, `place_*`, `modify_*`, `cancel_order` — and for each asynchronous order state transition (fill, cancel, reject) observed after `place_order` returns. Every entry captures the timestamp, the trading mode, the account, the parameters, the response, and the MCP `clientInfo` (self-reported by the agent client during `initialize`).

## Considered options

- **SQLite for queryability.** Rejected — overhead and schema migration burden outweigh the win for v1; the audit log is for human review and `jq`-able log lines cover that. Revisit if real users need cross-session analytical queries.
- **Include reads (`list_positions`, `get_quote`, etc.).** Rejected — high volume, low audit value. Order-mutating calls are the only safety-critical record.
- **Fail-closed on audit write failure.** Rejected — better to let the trade through than block trading on a logging issue; the failure is surfaced loudly via a `warnings` field on the tool response and an `stderr` message.
- **Cryptographic signing / agent identity verification.** Rejected — the MCP `clientInfo` is self-reported and that's the best we get; the audit log is for human review, not authentication.

## Consequences

- The log grows unbounded by default. v1 documents the rotation pattern (rotate at ~10 MB, keep 30 days) as operator responsibility; the adapter does not rotate itself. Revisit if real users complain.
- Sensitive data (account ID, position sizes, prices) lives in plaintext on disk. The `0600` mode is the only protection. Disk-level encryption is the user's problem.
- Async-outcome rows mean the log contains some entries that aren't tied to a specific tool call — they're observed state changes. Tooling that reads the log must accept that.
