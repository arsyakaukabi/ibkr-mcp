# Two-layer trading safety: paper-default trading mode + preview ticket

The adapter exposes order placement to LLM agent clients, which can hallucinate or misread context as instructions; orders move real money. We adopt two independent safety layers. (1) **Trading mode** (`paper` or `live`) is set at adapter startup and cannot be changed from inside an MCP session — switching to live requires the operator to restart with new config. (2) Every order goes through a two-step preview/confirm flow: `preview_order` returns a short-lived single-use **preview ticket**; `place_order` only accepts that ticket. Both layers apply in both modes.

## Considered options

- **Paper-only v1.** Rejected — the product goal explicitly includes live trading from the start.
- **Out-of-band live toggle only, no preview ticket.** Rejected — blocks between-session privilege escalation but lets an autonomous agent batch many live orders in a single turn once the operator enables live mode.
- **Preview ticket only, no mode toggle.** Rejected — an agent could chain `preview_order` → `place_order` in one turn against a live account if the operator's session were already configured for live trading via tool args.

## Consequences

- The MCP tool catalog has paired tools per order action (`preview_*` + `place_*`), increasing surface but improving auditability of every order in the chat transcript.
- Fully-autonomous, hands-off trading is constrained by design. Users who want unattended trading must script it outside MCP; the adapter is not the right shape for that.
- Switching live ↔ paper requires an adapter restart. This is deliberate: it keeps a human in the loop at the live boundary.
