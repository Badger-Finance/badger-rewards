from subgraph.queries.tokens import fetch_token_balances, fetch_fuse_pool_balances
from subgraph.subgraph_utils import make_gql_client
from helpers.constants import BADGER, DIGG
from badger_api.requests import fetch_token_prices
from collections import Counter
from typing import Dict, Tuple


def token_snapshot(chain: str, block: int) -> Tuple[Dict[str, float], Dict[str, float]]:
    token_client = make_gql_client(f"tokens-{chain}")
    return fetch_token_balances(token_client, block)


def fuse_snapshot(chain: str, block: int):
    fuse_client = make_gql_client("fuse")
    return fetch_fuse_pool_balances(fuse_client, chain, block)


def token_snapshot_usd(chain: str, block: int):

    fuse_balances = fuse_snapshot(chain, block)
    print(fuse_balances)
    badger_balances, digg_balances = token_snapshot(chain, block)
    # Account for tokens loaned in fuse
    if fuse_balances:
        fuse_badger = fuse_balances.get(BADGER, {})
        fuse_digg = fuse_balances.get(DIGG, {})
        badger_balances = Counter(fuse_badger) + Counter(badger_balances)
        digg_balances = Counter(fuse_digg) + Counter(digg_balances)

    return convert_tokens_to_usd(badger_balances, digg_balances)


def convert_tokens_to_usd(badger, digg):

    prices = fetch_token_prices()
    total = {}

    for addr, bal in badger.items():
        total[addr.lower()] = bal * prices[BADGER]

    for addr, bal in digg.items():
        if addr not in total:
            total[addr.lower()] = 0
        total[addr.lower()] += bal * prices[DIGG]
    return total
