from typing import Counter, Dict, Tuple

from config.constants.addresses import BADGER, DIGG
from helpers.enums import Network
from rewards.classes.Snapshot import Snapshot
from subgraph.queries.tokens import (
    fetch_across_balances,
    fetch_fuse_pool_balances,
    fetch_token_balances,
    fetch_fuse_pool_token
)
from subgraph.subgraph_utils import make_gql_client


def token_snapshot(chain: str, block: int) -> Tuple[Snapshot, Snapshot]:
    token_client = make_gql_client(f"tokens-{chain}")

    badger_bals, digg_bals = fetch_token_balances(token_client, block, chain)
    across_bals = fetch_across_balances(block, chain)

    fuse_badger_bals = fetch_fuse_pool_token(chain, block, BADGER)
    fuse_digg_bals = fetch_fuse_pool_token(chain, block, DIGG)

    cumulative_badger_bals = Counter(badger_bals) + Counter(across_bals) + Counter(fuse_badger_bals)
    cumulative_digg_bals = Counter(digg_bals) + Counter(fuse_digg_bals)

    return Snapshot(BADGER, cumulative_badger_bals), Snapshot(DIGG, cumulative_digg_bals)


def fuse_snapshot_of_token(chain: Network, block: int, token: str) -> Snapshot:
    bals = fetch_fuse_pool_token(chain, block, token)
    return Snapshot(token, bals)

def token_snapshot_usd(
    chain: str, block: int
) -> Tuple[Dict[str, float], Dict[str, float]]:

    badger_snapshot, digg_snapshot = token_snapshot(chain, block)
    return (
        badger_snapshot.convert_to_usd(chain).balances,
        digg_snapshot.convert_to_usd(chain).balances,
    )
