from pathlib import Path

import pytest

from ibkr_mcp.config import ConfigError, load_config


def test_load_config_defaults_match_compose_paper_gateway():
    """With no env vars set, the adapter must boot pointed at the paper IB Gateway
    that the bundled docker-compose template exposes. This is the zero-config
    promise: a user who runs `docker compose up` and then `uvx ibkr-mcp` with
    an empty env block gets a working adapter.
    """
    config = load_config({})

    assert config.gateway_host == "127.0.0.1"
    assert config.gateway_port == 4002
    assert config.client_id == 1
    assert config.trading_mode == "paper"
    assert config.account_id is None
    assert config.audit_log_path is None


def test_load_config_reads_all_env_overrides():
    """When every IBKR_* env var is set, the resulting Config reflects them all,
    with string-to-int conversion for the port and clientId, and string-to-Path
    for the audit log location.
    """
    config = load_config(
        {
            "IBKR_GATEWAY_HOST": "ib.example.com",
            "IBKR_GATEWAY_PORT": "4001",
            "IBKR_CLIENT_ID": "7",
            "IBKR_TRADING_MODE": "live",
            "IBKR_ACCOUNT_ID": "U1234567",
            "IBKR_AUDIT_LOG_PATH": "/var/log/ibkr-mcp/audit.jsonl",
        }
    )

    assert config.gateway_host == "ib.example.com"
    assert config.gateway_port == 4001
    assert config.client_id == 7
    assert config.trading_mode == "live"
    assert config.account_id == "U1234567"
    assert config.audit_log_path == Path("/var/log/ibkr-mcp/audit.jsonl")


def test_load_config_rejects_invalid_trading_mode():
    """IBKR_TRADING_MODE must be 'paper' or 'live'. Anything else fails at
    startup so the adapter can't boot into an undefined trading mode — the
    ADR-0001 safety contract depends on the mode being one of those two values.
    The error must name both the bad value and the valid choices.
    """
    with pytest.raises(ConfigError) as exc_info:
        load_config({"IBKR_TRADING_MODE": "demo"})

    message = str(exc_info.value)
    assert "demo" in message
    assert "paper" in message
    assert "live" in message


@pytest.mark.parametrize("bad_port", ["abc", "-1", "0", "65536", ""])
def test_load_config_rejects_invalid_gateway_port(bad_port):
    """IBKR_GATEWAY_PORT must be a TCP port (integer in 1..65535). Non-integer
    strings, zero, negative numbers, and out-of-range values are all rejected
    at startup so the adapter doesn't try to connect to an impossible socket.
    """
    with pytest.raises(ConfigError):
        load_config({"IBKR_GATEWAY_PORT": bad_port})


@pytest.mark.parametrize("bad_client_id", ["abc", "-1", ""])
def test_load_config_rejects_invalid_client_id(bad_client_id):
    """IBKR_CLIENT_ID must be a non-negative integer (clientId=0 is reserved
    for the master TWS/Gateway connection, so it's valid; negative values
    and non-integer strings are not).
    """
    with pytest.raises(ConfigError):
        load_config({"IBKR_CLIENT_ID": bad_client_id})
