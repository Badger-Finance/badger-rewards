import requests
from badger_api.config import urls
import concurrent.futures
from typing import List


def fetch_claimable(page: int):
    """
    Fetch claimable data from account data
    :param page: page to fetch data from
    """
    data = requests.get(f"{urls['staging']}/accounts/allClaimable?page={page}").json()
    return data


def fetch_total_claimable_pages():
    return fetch_claimable(1)["maxPage"]


def fetch_all_claimable_balances():
    """
    Fetch the claimable balances by fetching in parallel

    """
    results = {}
    total_pages = fetch_total_claimable_pages()
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [
            executor.submit(fetch_claimable, page=p) for p in range(1, total_pages)
        ]
        for future in concurrent.futures.as_completed(futures):
            data = future.result()["rewards"]
            results = {**results, **data}
    print(results)
    return results
