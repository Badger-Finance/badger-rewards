from typing import Counter, Dict, Tuple

from config.constants.addresses import DIGG
from config.constants.chain_mappings import NETWORK_TO_BADGER_TOKEN
from helpers.enums import Network
from rewards.classes.Snapshot import Snapshot
from subgraph.queries.tokens import (
    fetch_across_balances,
    fetch_token_balances,
    fetch_fuse_pool_token,
)


def token_snapshot(chain: str, block: int) -> Tuple[Snapshot, Snapshot]:
    badger_token_address = NETWORK_TO_BADGER_TOKEN[chain]
    badger_bals, digg_bals = fetch_token_balances(block, chain)
    across_bals = fetch_across_balances(block, chain)

    fuse_badger_bals = fetch_fuse_pool_token(chain, block, badger_token_address)
    fuse_digg_bals = fetch_fuse_pool_token(chain, block, DIGG)

    cumulative_badger_bals = (
        Counter(badger_bals) + Counter(across_bals) + Counter(fuse_badger_bals)
    )
    cumulative_digg_bals = Counter(digg_bals) + Counter(fuse_digg_bals)

    return (
        Snapshot(badger_token_address, cumulative_badger_bals),
        Snapshot(DIGG, cumulative_digg_bals),
    )


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
