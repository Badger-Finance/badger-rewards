from decimal import Decimal
from functools import lru_cache
from typing import Dict, Optional, Tuple

from badger_api.config import get_api_base_path
from helpers.enums import Network
from helpers.http_client import http_client

badger_api = get_api_base_path()


class InvalidAPIKeyException(Exception):
    pass


def fetch_ppfs() -> Optional[Tuple[Decimal, Decimal]]:
    """
    Fetch ppfs for bbadger and bdigg
    """
    setts = http_client.get(f"{badger_api}/vaults")
    if not setts:
        return
    badger = [sett for sett in setts if sett["asset"] == "BADGER"][0]
    digg = [sett for sett in setts if sett["asset"] == "DIGG"][0]
    if "pricePerFullShare" not in badger:
        raise InvalidAPIKeyException("BADGER missing pricePerFullShare key")
    if "pricePerFullShare" not in digg:
        raise InvalidAPIKeyException("DIGG missing pricePerFullShare key")

    return (
        Decimal(str(badger["pricePerFullShare"])),
        Decimal(str(digg["pricePerFullShare"])),
    )


@lru_cache
def fetch_token_prices(chain: Network, api_url: str = badger_api) -> Dict[str, float]:
    """
    Fetch token prices for sett tokens for a specific chain
    """
    return http_client.get(f"{api_url}/prices?chain={chain}")


@lru_cache
def fetch_token_names(chain: Network) -> Optional[Dict]:
    return http_client.get(f"{badger_api}/tokens?chain={chain}")


def fetch_token(chain: Network, token: str) -> Optional[Dict]:
    token_names = fetch_token_names(chain)
    return token_names.get(token, {}) if token_names else None


def fetch_token_decimals(chain: Network, token: str) -> int:
    token = fetch_token(chain, token)
    return token.get("decimals", 0)
