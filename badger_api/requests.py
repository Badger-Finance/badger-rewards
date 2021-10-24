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


def fetch_account_data(address: str):
    """
    Fetch data from account data
    :param address: address whose information is required
    """
    data = (
        requests.get(f"{badger_api}/accounts/{address}")
        .json()
        .get("claimableBalances", [])
    )
    return data


def fetch_claimable_balances(addresses: List[str]):
    """
    Fetch the claimable balances for a list of address
    by fetching in parallel

    :param addresses: list of addresses whose balances we want
    """
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures_to_addr = {
            executor.submit(fetch_account_data, address=addr): addr
            for addr in addresses
        }
        for future in concurrent.futures.as_completed(futures_to_addr):
            addr = futures_to_addr[future]
            data = future.result()
            results[addr] = data
    return results
