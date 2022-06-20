from functools import lru_cache
from typing import Dict, Optional, Tuple

from badger_api.config import get_api_base_path
from config.constants.emissions import BOOST_CHAINS
from helpers.enums import Network
from helpers.http_client import http_client

badger_api = get_api_base_path()


class InvalidAPIKeyException(Exception):
    pass


def fetch_ppfs() -> Optional[Tuple[float, float]]:
    """
    Fetch ppfs for bbadger and bdigg
    """
    setts = http_client.get(f"{badger_api}/setts")
    if not setts:
        return
    badger = [sett for sett in setts if sett["asset"] == "BADGER"][0]
    digg = [sett for sett in setts if sett["asset"] == "DIGG"][0]
    if "pricePerFullShare" not in badger:
        raise InvalidAPIKeyException("BADGER missing pricePerFullShare key")
    if "pricePerFullShare" not in digg:
        raise InvalidAPIKeyException("DIGG missing pricePerFullShare key")

    return badger["pricePerFullShare"], digg["pricePerFullShare"]


@lru_cache
def fetch_token_prices() -> Dict[str, float]:
    """
    Fetch token prices for sett tokens
    """
    chains = BOOST_CHAINS
    prices = {}
    for chain in chains:
        chain_prices = http_client.get(f"{badger_api}/prices?chain={chain}")
        if not chain_prices:
            continue
        prices = {**prices, **chain_prices}

    return prices


@lru_cache
def fetch_token_names(chain: Network) -> Optional[Dict]:
    return http_client.get(f"{badger_api}/tokens?chain={chain}")


def fetch_token(chain: Network, token: str) -> Optional[Dict]:
    token_names = fetch_token_names(chain)
    return token_names.get(token, {}) if token_names else None


def fetch_token_decimals(chain: Network, token: str) -> int:
    token = fetch_token(chain, token)
    return token.get("decimals", 0)
