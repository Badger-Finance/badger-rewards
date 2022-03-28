from typing import Counter, Dict, Tuple

from config.constants.addresses import BADGER, DIGG
from rewards.classes.Snapshot import Snapshot
from subgraph.queries.tokens import (
    fetch_across_balances,
    fetch_fuse_pool_balances,
    fetch_token_balances,
)
from subgraph.subgraph_utils import make_gql_client


def token_snapshot(chain: str, block: int) -> Tuple[Snapshot, Snapshot]:
    client = make_gql_client(f"tokens-{chain}")
    badger_bals, digg_bals = fetch_token_balances(client, block, chain)
    across_bals = fetch_across_balances(block, chain)
    cumulative_badger_bals = Counter(badger_bals) + Counter(across_bals)
    return Snapshot(BADGER, cumulative_badger_bals), Snapshot(DIGG, digg_bals)


def fuse_snapshot(chain: str, block: int) -> Dict[str, Snapshot]:
    fuse_client = make_gql_client("fuse")
    fuse_bals = fetch_fuse_pool_balances(fuse_client, chain, block)
    fuse_snapshots = {}
    for token, bals in fuse_bals.items():
        fuse_snapshots[token] = Snapshot(token, bals)

    return fuse_snapshots


def token_snapshot_usd(
    chain: str, block: int
) -> Tuple[Dict[str, float], Dict[str, float]]:

    fuse_snapshots = fuse_snapshot(chain, block)
    badger_snapshot, digg_snapshot = token_snapshot(chain, block)
    # Account for tokens loaned in fuse
    if len(fuse_snapshots) > 0:
        fuse_badger = fuse_snapshots.get(BADGER, Snapshot(BADGER, {}))
        fuse_digg = fuse_snapshots.get(DIGG, Snapshot(DIGG, {}))

        badger_snapshot = fuse_badger + badger_snapshot
        digg_snapshot = fuse_digg + digg_snapshot

    return (
        badger_snapshot.convert_to_usd(chain).balances,
        digg_snapshot.convert_to_usd(chain).balances,
    )
