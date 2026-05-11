from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping


class ConfigError(ValueError):
    """Raised when the environment-supplied configuration is invalid."""


@dataclass(frozen=True)
class Config:
    gateway_host: str
    gateway_port: int
    client_id: int
    trading_mode: Literal["paper", "live"]
    account_id: str | None
    audit_log_path: Path | None


def _read_int_env(
    env: Mapping[str, str],
    name: str,
    default: str,
    *,
    min_value: int,
    max_value: int | None = None,
) -> int:
    raw = env.get(name, default)
    constraint = (
        f"in {min_value}..{max_value}" if max_value is not None else f">= {min_value}"
    )
    try:
        value = int(raw)
    except ValueError:
        raise ConfigError(f"{name} must be an integer {constraint}, got {raw!r}")
    if value < min_value or (max_value is not None and value > max_value):
        raise ConfigError(f"{name} must be an integer {constraint}, got {value}")
    return value


def load_config(env: Mapping[str, str]) -> Config:
    trading_mode = env.get("IBKR_TRADING_MODE", "paper")
    if trading_mode not in ("paper", "live"):
        raise ConfigError(
            f"IBKR_TRADING_MODE must be 'paper' or 'live', got {trading_mode!r}"
        )

    gateway_port = _read_int_env(
        env, "IBKR_GATEWAY_PORT", "4002", min_value=1, max_value=65535
    )
    client_id = _read_int_env(env, "IBKR_CLIENT_ID", "1", min_value=0)

    audit_log_path = env.get("IBKR_AUDIT_LOG_PATH")
    return Config(
        gateway_host=env.get("IBKR_GATEWAY_HOST", "127.0.0.1"),
        gateway_port=gateway_port,
        client_id=client_id,
        trading_mode=trading_mode,
        account_id=env.get("IBKR_ACCOUNT_ID"),
        audit_log_path=Path(audit_log_path) if audit_log_path else None,
    )
