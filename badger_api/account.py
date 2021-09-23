import requests
from badger_api.config import urls
import concurrent.futures
from typing import List


def fetch_account_data(address: str):
    """
    Fetch data from account data
    :param address: address whose information is required
    """
    data = (
        requests.get(f"{urls['staging']}/accounts/{address}")
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
