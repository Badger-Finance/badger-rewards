import concurrent.futures
from functools import lru_cache
from typing import Dict, List, Optional, Tuple, Union

from badger_api.config import get_api_base_path
from helpers.constants import BOOST_CHAINS
from helpers.http_client import http_client

badger_api = get_api_base_path()


def fetch_ppfs() -> Optional[Tuple[float, float]]:
    """
    Fetch ppfs for bbadger and bdigg
    """
    setts = http_client.get(f"{badger_api}/setts")
    if not setts:
        return
    badger = [sett for sett in setts if sett["asset"] == "BADGER"][0]
    digg = [sett for sett in setts if sett["asset"] == "DIGG"][0]
    return badger["ppfs"], digg["ppfs"]


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


def fetch_claimable(page: int, chain: str) -> Optional[Dict]:
    """
    Fetch claimable data from account data
    :param page: page to fetch data from
    """
    return http_client.get(f"{badger_api}/accounts/allClaimable?page={page}&chain={chain}")


def fetch_total_claimable_pages(chain: str) -> Optional[int]:
    response = fetch_claimable(1, chain)
    if not response:
        return
    return response["maxPage"]


def fetch_all_claimable_balances(chain: str) -> Optional[Dict]:
    """
    Fetch the claimable balances by fetching in parallel

    """

    results = {}
    total_pages = fetch_total_claimable_pages(chain)
    if not total_pages:
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [
            executor.submit(fetch_claimable, page=p, chain=chain)
            for p in range(0, total_pages + 1)
        ]
        for future in concurrent.futures.as_completed(futures):
            data = future.result()["rewards"]
            results = {**results, **data}
    return results


@lru_cache
def fetch_token_names(chain: str) -> Dict:
    response = http_client.get(f"{badger_api}/tokens?chain={chain}")
    if not response.ok:
        return
    return response.json()


def fetch_token(chain: str, token: str) -> Dict:
    token_names = fetch_token_names(chain)
    return token_names.get(token, {}) if token_names else None
