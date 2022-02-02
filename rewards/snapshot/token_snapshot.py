from typing import Dict, Tuple

from helpers.constants import BADGER, DIGG
from rewards.classes.Snapshot import Snapshot
from subgraph.queries.tokens import fetch_fuse_pool_balances, fetch_token_balances


def token_snapshot(chain: str, block: int) -> Tuple[Snapshot, Snapshot]:
    badger_bals, digg_bals = fetch_token_balances(block, chain)
    return Snapshot(BADGER, badger_bals), Snapshot(DIGG, digg_bals)


def fuse_snapshot(chain: str, block: int) -> Dict[str, Snapshot]:
    fuse_bals = fetch_fuse_pool_balances(chain, block)
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
