import requests
from badger_api.config import urls
import concurrent.futures


def fetch_claimable(page: int, chain: str):
    """
    Fetch claimable data from account data
    :param page: page to fetch data from
    """
    if chain == "eth":
        chain = "ethereum"

    data = requests.get(
        f"{urls['staging']}/accounts/allClaimable?page={page}&chain={chain}"
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
