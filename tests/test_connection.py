import pytest

from ibkr_mcp.connection import AccountBindingError, bind_account


def test_bind_account_single_account_no_request_binds_to_it():
    """Zero-friction common case: the login owns one account and the operator
    didn't set IBKR_ACCOUNT_ID. The adapter binds to the only candidate without
    complaint — this is what "zero-config first launch" depends on.
    """
    assert bind_account(["DU1234567"], requested=None) == "DU1234567"


def test_bind_account_multi_account_no_request_fails_listing_candidates():
    """If the login owns multiple accounts and IBKR_ACCOUNT_ID is unset, the
    adapter must refuse to start and surface the candidate accounts in the
    error so the operator knows what to choose (PRD story 27). The error
    must also name the IBKR_ACCOUNT_ID env var so the fix is actionable.
    """
    with pytest.raises(AccountBindingError) as exc_info:
        bind_account(["DU111", "DU222", "U555"], requested=None)

    message = str(exc_info.value)
    assert "DU111" in message
    assert "DU222" in message
    assert "U555" in message
    assert "IBKR_ACCOUNT_ID" in message


def test_bind_account_multi_account_with_matching_request_binds_to_it():
    """When IBKR_ACCOUNT_ID matches exactly one of the candidate accounts,
    the adapter binds to that specific account and ignores the others.
    """
    assert bind_account(["DU111", "DU222", "U555"], requested="DU222") == "DU222"


def test_bind_account_request_not_in_candidates_fails_with_helpful_error():
    """If IBKR_ACCOUNT_ID is set but doesn't match any candidate, the adapter
    must refuse to start and surface both what was requested and the actual
    candidate set so the operator can spot the typo at a glance.
    """
    with pytest.raises(AccountBindingError) as exc_info:
        bind_account(["DU111", "DU222"], requested="DU999")

    message = str(exc_info.value)
    assert "DU999" in message
    assert "DU111" in message
    assert "DU222" in message


def test_bind_account_empty_available_fails():
    """Defensive: if IBKR returns no accounts for this login (rare, but can
    happen with a misconfigured login or paper-only accounts during off-hours),
    the adapter must surface a clear error rather than crashing later with
    an IndexError on available[0].
    """
    with pytest.raises(AccountBindingError):
        bind_account([], requested=None)
