# IBKR MCP Adapter

An MCP server that exposes Interactive Brokers account and trading capabilities to LLM agent clients (Claude Code, Codex, Gemini, etc.). Aims to be cheap to set up and uniform to consume across agents.

## Language

**IBKR adapter**:
The MCP server in this repo. Translates MCP tool calls into IBKR API calls and shapes responses for LLM consumption.
_Avoid_: server, gateway, bridge, proxy (all overloaded with IBKR's own components — see below)

**Agent client**:
The LLM-side process that connects to the adapter over MCP (Claude Code, Codex, Gemini, etc.).
_Avoid_: client, user, LLM (ambiguous on their own)

**IB Gateway**:
IBKR's headless trading session — a lightweight, GUI-minimal alternative to TWS that hosts the socket API the adapter connects to. The user logs in once; the gateway holds the authenticated session.
_Avoid_: gateway (unqualified), TWS (TWS is the full desktop app and a separate process), Client Portal Gateway (that fronts a different IBKR API we are not using).

**Trading mode**:
A startup-time setting on the adapter, either `paper` or `live`. Determines which IBKR account the adapter routes orders to. Cannot be changed from inside an MCP session — the operator must restart the adapter with new config.
_Avoid_: account type, env, environment (all overloaded).

**Preview ticket**:
A short-lived, single-use token returned by `preview_order` and consumed by `place_order`. Encodes the proposed order's full specification (symbol, side, quantity, type, limit price, account, trading mode) and an estimated cost / margin impact. Required for every order submission, in both paper and live mode.
_Avoid_: token, draft, intent (all reusable elsewhere or too generic).

**Instrument**:
A tradable thing the adapter knows how to quote and route. In v1: an **equity** (stock or ETF) or an **option** (equity/ETF option contract identified by underlying, expiry, strike, and right C/P).
_Avoid_: security, asset, ticker (each is a partial synonym used inconsistently by IBKR's own docs).

**Option chain**:
The set of listed option contracts for a single underlying instrument across all expiries and strikes. Queried as a snapshot, not streamed.
_Avoid_: chain (unqualified), option ladder.

**Bracket order**:
A parent entry order plus a take-profit child and a stop-loss child, submitted as one atomic OCA group on the IBKR side. From the adapter's perspective, a bracket is a single preview ticket that carries the full parent+children shape.
_Avoid_: OCO (technically the children are an OCA group, not strict OCO; "bracket" is IBKR's name for the whole construct).

**Terminal state**:
An order state from which no further transitions occur: `filled`, `cancelled`, `rejected`. `place_order` returns as soon as the order reaches a terminal state or the configured timeout (~5s default) elapses.
_Avoid_: final, done, closed.

**Resting state**:
An order state where the order is live with IBKR but not yet filled: `submitted`, `pre-submitted`, `working`. Returned by `place_order` when the timeout elapses without reaching a terminal state; the agent then uses `get_order_status` to poll.
_Avoid_: pending (overloaded with "we haven't sent it yet").

## Relationships

- The **agent client** speaks MCP to the **IBKR adapter**.
- The **IBKR adapter** speaks the TWS socket API to **IB Gateway**.
- **IB Gateway** holds the user's authenticated IBKR session and forwards trading/data calls to IBKR servers.

## Example dialogue

> **Dev:** "When the **agent client** calls `preview_equity_order(symbol='AAPL', side='BUY', quantity=100, type='LMT', limit=175.00)`, what does the **preview ticket** actually carry?"
>
> **Domain expert:** "The full proposed order — **instrument**, side, quantity, order type, limit price — plus the **trading mode** that's active, the bound account, and an estimated cost/margin impact. Single-use, ~60s expiry. `place_order` won't accept anything else."
>
> **Dev:** "If **IB Gateway** is in paper mode but I want to test what live submission looks like, can I pass `trading_mode='live'` to `preview_order`?"
>
> **Domain expert:** "No — the **trading mode** is fixed at adapter startup, not negotiable per call. That's the whole point of ADR-0001's first layer. To test live behaviour you restart the adapter pointing at the live Gateway port."
>
> **Dev:** "What if `place_order` runs out the 5s timeout and the order is still alive on IBKR but unfilled?"
>
> **Domain expert:** "It returns with the **resting state** (`working` or `submitted`) and an `orderId`. The agent then polls `get_order_status` until the order reaches a **terminal state** — `filled`, `cancelled`, or `rejected`. The audit log captures the async transitions even though they weren't returned by the original `place_order` call."
>
> **Dev:** "And a **bracket order** — does it produce three preview tickets or one?"
>
> **Domain expert:** "One. The bracket is a single intent: parent entry + take-profit child + stop-loss child, submitted as one OCA group to IBKR. The preview ticket carries all three legs together."

## Flagged ambiguities

- "MCP server" was used initially — kept as the technical role but in conversation we use **IBKR adapter** so it doesn't collide with IBKR-side components like _IB Gateway_ or _Client Portal Gateway_ which are also "servers".
