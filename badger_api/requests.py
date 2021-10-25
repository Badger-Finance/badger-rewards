import requests
from badger_api.config import get_api_base_path
from typing import Tuple, Dict, List
import concurrent.futures
from functools import lru_cache

badger_api = get_api_base_path()


def fetch_ppfs() -> Tuple[float, float]:
    """
    Fetch ppfs for bbadger and bdigg
    """
    response = requests.get(f"{badger_api}/setts").json()
    badger = [s for s in response if s["asset"] == "BADGER"][0]
    digg = [s for s in response if s["asset"] == "DIGG"][0]
    return badger["ppfs"], digg["ppfs"]


@lru_cache()
def fetch_token_prices() -> Dict[str, float]:
    """
    Fetch token prices for sett tokens
    """
    chains = ["eth", "matic", "arbitrum"]
    prices = {}
    for chain in chains:
        chain_prices = requests.get(f"{badger_api}/prices?chain={chain}").json()
        prices = {**prices, **chain_prices}

    return prices


def fetch_claimable(page: int, chain: str):
    """
    Fetch claimable data from account data
    :param page: page to fetch data from
    """
    data = requests.get(
        f"{badger_api}/accounts/allClaimable?page={page}&chain={chain}"
    ).json()
    return data

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
