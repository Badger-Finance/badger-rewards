from decimal import Decimal
from config.constants.emissions import DIGG_BOOST_VAULTS
from helpers.enums import Network
from typing import Dict
from rewards.snapshot.chain_snapshot import sett_snapshot


def digg_snapshot_usd(chain: Network, block: int) -> Dict[str, Decimal]:
    if chain == Network.Ethereum:
        digg_snaps = [sett_snapshot(chain, block, v) for v in DIGG_BOOST_VAULTS]
        return sum([s.convert_to_usd(chain) for s in digg_snaps]).balances
    else:
        return {}
