import concurrent.futures
from functools import lru_cache
from typing import Dict, Tuple

from badger_api.config import get_api_base_path
from helpers import http
from helpers.constants import BOOST_CHAINS

badger_api = get_api_base_path()


def fetch_ppfs() -> Tuple[float, float]:
    """
    Fetch ppfs for bbadger and bdigg
    """
    response = http.get(f"{badger_api}/setts")
    setts = response.json()
    if not setts:
        return
    badger = [sett for sett in setts if sett["asset"] == "BADGER"][0]
    digg = [sett for sett in setts if sett["asset"] == "DIGG"][0]
    return badger["ppfs"], digg["ppfs"]


@lru_cache()
def fetch_token_prices() -> Dict[str, float]:
    """
    Fetch token prices for sett tokens
    """
    chains = BOOST_CHAINS
    prices = {}
    for chain in chains:
        response = http.get(f"{badger_api}/prices?chain={chain}")
        chain_prices = response.json()
        prices = {**prices, **chain_prices}

    return prices


def fetch_claimable(page: int, chain: str):
    """
    Fetch claimable data from account data
    :param page: page to fetch data from
    """
    response = http.get(f"{badger_api}/accounts/allClaimable?page={page}&chain={chain}")
    return response.json()


def fetch_total_claimable_pages(chain: str) -> int:
    return fetch_claimable(1, chain)["maxPage"]


def fetch_all_claimable_balances(chain: str):
    """
    Fetch the claimable balances by fetching in parallel

    """

    results = {}
    total_pages = fetch_total_claimable_pages(chain)
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
def fetch_token_names(chain: str):
    return http.get(f"{badger_api}/tokens?chain={chain}").json()


def fetch_token(chain: str, token: str):
    token_names = fetch_token_names(chain)
    return token_names.get(token, {})
