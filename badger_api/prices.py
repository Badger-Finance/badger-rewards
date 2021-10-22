import requests
from badger_api.config import get_api_url, urls
from typing import Tuple, Dict
from functools import lru_cache


def fetch_ppfs() -> Tuple[float, float]:
    """
    Fetch ppfs for bbadger and bdigg
    """
    response = requests.get(f"{get_api_url()}/setts").json()
    badger = [s for s in response if s["asset"] == "BADGER"][0]
    digg = [s for s in response if s["asset"] == "DIGG"][0]
    return badger["ppfs"], digg["ppfs"]


@lru_cache(maxsize=None)
def fetch_token_prices() -> Dict[str, float]:
    """
    Fetch token prices for sett tokens
    """
    chains = ["eth", "bsc", "matic", "arbitrum"]
    prices = {}
    for chain in chains:
        chain_prices = requests.get(f"{get_api_url()}/prices?chain={chain}").json()
        prices = {**prices, **chain_prices}
    return prices
