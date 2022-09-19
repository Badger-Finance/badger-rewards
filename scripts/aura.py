"""
A script to calculate % portions of user balance per given snapshot
for FBVECVX, Rari and BVECVX LP Pool
"""

import math
from decimal import Decimal
from typing import Dict

import simplejson as json

from config.constants import addresses
from helpers.enums import Network
from logging_utils import logger
from rewards.boost.boost_utils import get_bvecvx_lp_ppfs
from rewards.boost.boost_utils import get_bvecvx_lp_ratio
from rewards.classes.Snapshot import Snapshot
from rewards.snapshot.chain_snapshot import sett_snapshot
from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.snapshot.token_snapshot import fuse_snapshot_of_token

AURA_SNAPSHOT_BLOCK = 14829454
MAX_TOLERANCE_THRESHOLD = Decimal(0.001)


def snapshot_to_percentages(snapshot: Snapshot):
    percentages = {}
    for address, number in snapshot:
        percentage = snapshot.percentage_of_total(address)
        # Filter out very small amounts
        if percentage > Decimal(0.000001):
            percentages[address] = percentage
    # Sort by biggest balance
    return dict(sorted(percentages.items(), key=lambda item: item[1], reverse=True))


def does_snapshot_percentages_sum_up(bvecvx_snap_data: Dict, address: str) -> bool:
    """
    Function to make sure that all percentages add up to 100%
    """
    wallets = bvecvx_snap_data[address]
    accumulated = Decimal(0)
    for wallet_percentage in wallets.values():
        accumulated += Decimal(wallet_percentage)
    logger.print(f"Accumulated {accumulated}% for {address}")
    # Make sure values are different no more than by MAX_TOLERANCE_THRESHOLD%
    # because we filter out some small balances
    return math.isclose(Decimal(1), accumulated, abs_tol=MAX_TOLERANCE_THRESHOLD)


if __name__ == "__main__":
    """
    To run this:
        First, do $ source venv/bin/activate
        Then: $ python -m scripts.aura
    """
    chain = Network.Ethereum
    all_claims = claims_snapshot(chain, AURA_SNAPSHOT_BLOCK)
    fuse_bvecvx = fuse_snapshot_of_token(chain, AURA_SNAPSHOT_BLOCK, addresses.BVECVX)
    lp_bvecvx = sett_snapshot(chain, AURA_SNAPSHOT_BLOCK, addresses.BVECVX_CVX_LP_SETT)
    claimable_bvecvx = all_claims[addresses.BVECVX]
    ratio = get_bvecvx_lp_ratio()
    ppfs = get_bvecvx_lp_ppfs()
    # For each address holding the LP, multiply their holdings by the current ratio of bveCVX :
    # CVX and the pricePerFullShare of the vault to determine underlying holdings
    for addr, value in lp_bvecvx:
        lp_bvecvx.boost_balance(addr, ratio)
        lp_bvecvx.boost_balance(addr, ppfs)

    bvecvx_data = {}
    bvecvx_data[addresses.FBVECVX] = snapshot_to_percentages(fuse_bvecvx)
    bvecvx_data[addresses.BVECVX_CVX_LP_SETT] = snapshot_to_percentages(lp_bvecvx)
    bvecvx_data[addresses.ETH_BADGER_TREE] = snapshot_to_percentages(claimable_bvecvx)
    # Make sure all balanaces in % add up to 100%
    assert does_snapshot_percentages_sum_up(bvecvx_data, addresses.ETH_BADGER_TREE)
    assert does_snapshot_percentages_sum_up(bvecvx_data, addresses.FBVECVX)
    assert does_snapshot_percentages_sum_up(bvecvx_data, addresses.BVECVX_CVX_LP_SETT)

    with open('aura.json', 'w') as fp:
        json.dump(bvecvx_data, fp, use_decimal=True, indent=4)
