from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from trading_system.app.user_settings import HyperliquidCredentials

MAINNET_API_URL = "https://api.hyperliquid.xyz"
MAINNET_WS_URL = "wss://api.hyperliquid.xyz/ws"
TESTNET_API_URL = "https://api.hyperliquid-testnet.xyz"
TESTNET_WS_URL = "wss://api.hyperliquid-testnet.xyz/ws"


def normalize_network(value: str) -> str:
    lowered = (value or "mainnet").strip().lower()
    return "testnet" if lowered == "testnet" else "mainnet"


def default_api_url(network: str) -> str:
    return TESTNET_API_URL if normalize_network(network) == "testnet" else MAINNET_API_URL


def default_ws_url(network: str) -> str:
    return TESTNET_WS_URL if normalize_network(network) == "testnet" else MAINNET_WS_URL


def apply_network_defaults(credentials: HyperliquidCredentials) -> HyperliquidCredentials:
    network = normalize_network(credentials.network)
    api_url = credentials.api_url.strip() if credentials.api_url else ""
    ws_url = credentials.ws_url.strip() if credentials.ws_url else ""
    if not api_url or api_url in {MAINNET_API_URL, TESTNET_API_URL}:
        api_url = default_api_url(network)
    if not ws_url or ws_url in {MAINNET_WS_URL, TESTNET_WS_URL}:
        ws_url = default_ws_url(network)
    return credentials.model_copy(
        update={
            "network": network,
            "api_url": api_url,
            "ws_url": ws_url,
        }
    )
