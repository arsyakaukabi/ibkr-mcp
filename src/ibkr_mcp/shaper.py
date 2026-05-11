from typing import Literal


def shape_accounts(
    accounts: list[str], trading_mode: Literal["paper", "live"]
) -> list[dict]:
    return [
        {"account_id": account_id, "trading_mode": trading_mode}
        for account_id in accounts
    ]
