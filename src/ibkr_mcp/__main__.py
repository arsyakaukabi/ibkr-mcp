import os
import sys
from typing import Literal

from mcp.server.fastmcp import FastMCP

from ibkr_mcp.config import ConfigError, load_config
from ibkr_mcp.connection import AccountBindingError, IBKRConnection
from ibkr_mcp.shaper import shape_accounts

mcp = FastMCP("ibkr-mcp")

_bound_account: str | None = None
_trading_mode: Literal["paper", "live"] | None = None


@mcp.tool()
def list_accounts() -> list[dict]:
    """List the IBKR account(s) bound to this adapter, plus the active trading
    mode (paper or live). The trading mode is fixed at adapter startup; restart
    the adapter to switch.
    """
    assert _bound_account is not None and _trading_mode is not None
    return shape_accounts([_bound_account], _trading_mode)


def _die(message: str, code: int = 1) -> None:
    print(f"ibkr-mcp: {message}", file=sys.stderr)
    sys.exit(code)


def main() -> None:
    global _bound_account, _trading_mode

    try:
        config = load_config(os.environ)
    except ConfigError as e:
        _die(f"invalid configuration: {e}", code=2)

    connection = IBKRConnection(config)
    try:
        connection.connect()
    except ConnectionRefusedError:
        _die(
            f"could not connect to IB Gateway at "
            f"{config.gateway_host}:{config.gateway_port}. "
            f"Is IB Gateway running? If you're using the bundled docker-compose, "
            f"run `docker compose up -d` first.",
        )
    except OSError as e:
        _die(
            f"network error connecting to IB Gateway at "
            f"{config.gateway_host}:{config.gateway_port}: {e}",
        )
    except AccountBindingError as e:
        _die(f"account binding failed: {e}", code=3)

    _bound_account = connection.bound_account
    _trading_mode = config.trading_mode
    try:
        mcp.run()
    finally:
        connection.disconnect()


if __name__ == "__main__":
    main()
