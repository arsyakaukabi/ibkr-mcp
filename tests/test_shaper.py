from ibkr_mcp.shaper import shape_accounts


def test_shape_accounts_returns_llm_first_list_with_trading_mode():
    """The list_accounts tool surfaces each account plus the active trading
    mode so the agent client knows in-band whether it's operating against
    paper or live. This mirrors the out-of-band ADR-0001 startup setting:
    the agent reads it on every list_accounts call rather than guessing.
    """
    result = shape_accounts(["DU1234567"], trading_mode="paper")

    assert result == [{"account_id": "DU1234567", "trading_mode": "paper"}]
