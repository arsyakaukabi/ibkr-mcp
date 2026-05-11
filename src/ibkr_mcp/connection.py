import ib_async

from ibkr_mcp.config import Config


class AccountBindingError(ValueError):
    """Raised when the adapter cannot decide which IBKR account to bind to
    at startup. Carries enough context for the operator to fix the env.
    """


def bind_account(available: list[str], requested: str | None) -> str:
    if not available:
        raise AccountBindingError(
            "The IBKR login returned no accounts. Check that the login owns "
            "at least one account, or that the gateway is connected to the "
            "right environment (paper vs live)."
        )
    if requested is None and len(available) > 1:
        raise AccountBindingError(
            "IBKR_ACCOUNT_ID is not set and the login owns multiple accounts: "
            f"{', '.join(available)}. Set IBKR_ACCOUNT_ID to one of these."
        )
    if requested is not None and requested not in available:
        raise AccountBindingError(
            f"IBKR_ACCOUNT_ID={requested!r} does not match any account on this login. "
            f"Available: {', '.join(available)}."
        )
    if requested is not None:
        return requested
    return available[0]


class IBKRConnection:
    """Owns the ib_async.IB lifecycle. Public interface stays small;
    all ib_async quirks live behind it.
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._ib = ib_async.IB()
        self.bound_account: str | None = None

    def connect(self) -> None:
        self._ib.connect(
            host=self._config.gateway_host,
            port=self._config.gateway_port,
            clientId=self._config.client_id,
        )
        managed = list(self._ib.managedAccounts())
        self.bound_account = bind_account(managed, self._config.account_id)

    def disconnect(self) -> None:
        if self._ib.isConnected():
            self._ib.disconnect()
