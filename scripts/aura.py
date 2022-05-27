import math
from typing import Dict

from rich.console import Console

from config.constants import addresses
from decimal import Decimal
from helpers.enums import Network
from rewards.boost.boost_utils import get_bvecvx_lp_ppfs, get_bvecvx_lp_ratio
from rewards.classes.Snapshot import Snapshot
from rewards.snapshot.chain_snapshot import sett_snapshot
from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.snapshot.token_snapshot import fuse_snapshot_of_token
import json


console = Console()


def snapshot_to_percentages(snapshot: Snapshot):
    percentages = {}
    console.print(snapshot.total_balance())
    for addr, number in snapshot:
        percentages[addr] = snapshot.percentage_of_total(addr) * 100
    return dict(sorted(percentages.items(), key=lambda item: item[1], reverse=True))


def does_snapshot_percentages_sum_up(bvecvx_snap_data: Dict, address: str) -> bool:
    """
    Function to make sure that all percentages add up to 100%
    """
    wallets = bvecvx_snap_data[address]
    accumulated = Decimal(0)
    for wallet_percentage in wallets.values():
        accumulated += Decimal(wallet_percentage)
    console.print(f"Accumulated {accumulated} for {address}")
    return math.isclose(Decimal(100), accumulated)


if __name__ == "__main__":
    bvecvx_data = {}
    block = 14848251
    chain = Network.Ethereum
    all_claims = claims_snapshot(chain, block)
    fuse_bvecvx = fuse_snapshot_of_token(chain, block, addresses.BVECVX)
    lp_bvecvx = sett_snapshot(chain, block, addresses.BVECVX_CVX_LP_SETT)
    claimable_bvecvx = all_claims[addresses.BVECVX]
    ratio = get_bvecvx_lp_ratio()
    ppfs = get_bvecvx_lp_ppfs()
    for addr, value in lp_bvecvx:
        lp_bvecvx.boost_balance(addr, ratio)
        lp_bvecvx.boost_balance(addr, ppfs)

    bvecvx_data[addresses.FBVECVX] = snapshot_to_percentages(fuse_bvecvx)
    bvecvx_data[addresses.BVECVX_CVX_LP_SETT] = snapshot_to_percentages(lp_bvecvx)
    bvecvx_data[addresses.ETH_BADGER_TREE] = snapshot_to_percentages(claimable_bvecvx)
    assert does_snapshot_percentages_sum_up(bvecvx_data, addresses.ETH_BADGER_TREE)
    assert does_snapshot_percentages_sum_up(bvecvx_data, addresses.FBVECVX)
    assert does_snapshot_percentages_sum_up(bvecvx_data, addresses.BVECVX_CVX_LP_SETT)

    class DecimalEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, Decimal):
                return str(o)
            return super(DecimalEncoder, self).default(o)
        
    with open('aura.json', 'w') as fp:
        json.dump(bvecvx_data, fp, cls=DecimalEncoder)
