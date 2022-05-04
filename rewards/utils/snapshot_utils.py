from decimal import Decimal
from config.constants.emissions import DIGG_BOOST_VAULTS
from helpers.enums import Network
from types import Dict
from rewards.snapshot.chain_snapshot import sett_snapshot


def digg_snapshot_usd(chain: Network, block: int) -> Dict[str, Decimal]:
    digg_snaps = [sett_snapshot(v, chain, block) for v in DIGG_BOOST_VAULTS]
    return sum([s.convert_to_usd(chain) for s in digg_snaps]).balances
