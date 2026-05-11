# IB Gateway via Docker

Optional helper for running **IB Gateway** via `gnzsnz/ib-gateway-docker` so you don't have to install IB Gateway desktop. Pair with the adapter installed via `uvx ibkr-mcp` — the adapter's zero-config defaults already point at the paper Gateway this compose exposes (`127.0.0.1:4002`).

## Prerequisites

- Docker and `docker compose` installed
- An IBKR account with API access enabled. Paper accounts are free; live accounts must be funded. Enable API in **Account Settings → API → Settings** (check "Enable ActiveX and Socket Clients", uncheck "Read-Only API" if you want trade execution).

## Quick start

1. Copy the env template and fill in your IBKR credentials:

   ```bash
   cp docker/.env.example docker/.env
   $EDITOR docker/.env
   ```

2. Start the Gateway:

   ```bash
   docker compose -f docker/compose.yml --env-file docker/.env up -d
   ```

3. Watch the container come up. It takes ~30–60s on first start for the Gateway to authenticate:

   ```bash
   docker compose -f docker/compose.yml logs -f ib-gateway
   ```

4. Once you see the Gateway is logged in, the adapter can connect with its zero-config defaults:

   ```bash
   uvx --from . ibkr-mcp        # from this repo
   # or, once published:
   uvx ibkr-mcp
   ```

## Configuration

The compose file reads from `docker/.env`. See `docker/.env.example` for every variable and its default. The two required ones are `TWS_USERID` and `TWS_PASSWORD`.

If you switch to live trading, set `TRADING_MODE=live` in `docker/.env` **and** `IBKR_TRADING_MODE=live` + `IBKR_GATEWAY_PORT=4001` in the adapter's env block. The two settings must agree (see ADR-0001).

## Stopping the Gateway

```bash
docker compose -f docker/compose.yml down
```

The session state lives in the `ibkr-gateway-data` Docker volume, so your login persists across restarts. To wipe the state (e.g. switching accounts), use `down -v`.

## Debugging via VNC

The Gateway runs a VNC server on `127.0.0.1:5900` for debugging the GUI. Connect with any VNC viewer (`vinagre`, `remmina`, macOS Screen Sharing). Set `VNC_SERVER_PASSWORD` in `.env` if you want a password; otherwise it accepts any password (localhost-only, so the risk is bounded).

## Nightly restart

IBKR forces a nightly restart of the Gateway session around midnight US Eastern. The container handles this automatically via the IBC tool baked into `gnzsnz/ib-gateway-docker`. The adapter will re-establish its socket when the Gateway comes back up.

## Multi-agent caveat

If you run multiple agent clients (Claude Code + Codex) against the same Gateway, each adapter process opens its own socket. The Gateway accepts one client connection per `clientId` by default. To support multiple, either:

- Set a distinct `IBKR_CLIENT_ID` per adapter instance (`1`, `2`, `3`, …), and configure the Gateway's API settings panel to accept multiple connections, **or**
- Run separate Gateway instances on different ports.

This is documented as a known caveat for v1 (PRD #1, story 33).
