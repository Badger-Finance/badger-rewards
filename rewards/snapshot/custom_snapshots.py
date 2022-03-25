from typing import Counter
from helpers.enums import Network
from rewards.snapshot.chain_snapshot import sett_snapshot
from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.snapshot.token_snapshot import token_snapshot
from config.constants import addresses

def badger_snapshot_usd(chain: Network, block: int) -> Counter:
    badger_snapshots = []
    badger_tokens , _ = token_snapshot(chain, block)
    badger_snapshots.append(badger_tokens)
    badger_snapshots.append(sett_snapshot(chain, block, addresses.BBADGER))
    badger_snapshots.append(sett_snapshot(chain, block, addresses.BSLP_BADGER_WBTC))
    badger_snapshots.append(sett_snapshot(chain, block, addresses.BUNI_BADGER_WBTC))
    badger_snapshots.append(claims_snapshot(chain, block).get(addresses.BADGER))
    usd_bals = Counter()
    for snapshot in badger_snapshots:
        usd_bals += Counter(snapshot.convert_to_usd(chain).balances)
    return usd_bals

def digg_snapshot(chain: Network, block: int):
    pass