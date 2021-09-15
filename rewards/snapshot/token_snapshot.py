from subgraph.client import fetch_fuse_pool_balances, fetch_token_balances
from subgraph.subgraph_utils import make_gql_client
from helpers.digg_utils import diggUtils
from helpers.constants import BADGER, DIGG, BBADGER, BDIGG
from badger_api.prices import fetch_ppfs, fetch_token_prices
from collections import Counter
from typing import Dict, Tuple


def token_snapshot(chain: str, block: int) -> Tuple[Dict[str, float], Dict[str, float]]:
    token_client = make_gql_client("tokens-{}".format(chain))
    return fetch_token_balances(token_client, diggUtils.sharesPerFragment, block)


def fuse_snapshot(chain: str, block: int):
    fuse_client = make_gql_client("fuse")
    return fetch_fuse_pool_balances(fuse_client, chain, block)


def token_snapshot_usd(chain: str, block: int):

    badger_ppfs, digg_ppfs = fetch_ppfs()

    fuse_balances = fuse_snapshot(chain, block)
    badger_balances, digg_balances = token_snapshot(chain, block)
    # Account for tokens loaned in fuse
    if fuse_balances:
        # fuse_balances[BBADGER] = {
        #    k: v * badger_ppfs for k, v in fuse_balances[BBADGER].items()
        # }
        fuse_badger = fuse_balances[BADGER]
        fuse_digg = fuse_balances[DIGG]
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
