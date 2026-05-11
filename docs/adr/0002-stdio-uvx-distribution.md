# Adapter ships as a uvx-installable PyPI package over stdio; IB Gateway runs separately

The product goal is "easy to consume by any MCP client" and "easy to set up". The adapter is published to PyPI and invoked via `uvx ibkr-mcp` from an agent client's MCP server config, using stdio transport only. IB Gateway is treated as a separate concern the user owns; we ship an optional `docker/compose.yml` that runs gnzsnz/ib-gateway-docker so first-time users can `docker compose up` to bring up Gateway, but the adapter itself does not download, configure, or orchestrate Gateway.

## Considered options

- **HTTP / SSE daemon transport.** Rejected for v1 — stdio is universally supported across MCP clients; HTTP support is patchier. Revisit only if multi-agent-on-one-Gateway shows up as a real user pain point.
- **Containerising the adapter itself.** Rejected — adds a Docker dependency without solving anything the optional Gateway-side compose file doesn't already cover. Breaks the canonical "paste this into mcp.json" install flow.
- **A first-run CLI that downloads and launches IB Gateway.** Rejected — IBKR's terms restrict bundling Gateway, and automating credentialed login for retail accounts is brittle and policy-risky.

## Consequences

- Adapter and Gateway have independent lifecycles. A user who already runs IB Gateway or TWS can ignore the compose file entirely.
- Each MCP session spawns its own adapter process, so the IBKR socket connection is re-established at every session start. Acceptable for stdio.
- Multiple simultaneous agent clients (e.g. Claude Code + Codex) will fight over Gateway's per-port client-connection limit unless the user configures Gateway for multiple connections and the adapter rotates its `clientId`. This must be documented; it is not enforced in code.
