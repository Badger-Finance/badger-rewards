from decimal import Decimal
from rich.console import Console

import config.constants.addresses as addresses
from config.constants.chain_mappings import UNCLAIMED_REWARDS_TOKENS
from helpers.enums import Network
from rewards.snapshot.chain_snapshot import sett_snapshot
from rewards.classes.RewardsList import RewardsList
from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.snapshot.token_snapshot import fuse_snapshot_of_token
from rewards.utils.rewards_utils import distribute_rewards_from_total_snapshot

console = Console()


def unclaimed_rewards_handler(amount: Decimal, token: str, sett: str, block: int):
    console.log(f"Distributing {amount} of {token} to unclaimed rewards")
    claimable = claims_snapshot(Network.Ethereum, block)
    if sett not in claimable:
        console.log("Sett not in claimable")
        return RewardsList()
    if sett in UNCLAIMED_REWARDS_TOKENS[Network.Ethereum]:
        console.log("Sett in claimable")
        console.log(claimable[sett].balances)
        return distribute_rewards_from_total_snapshot(amount, claimable[sett], token, block)


def bvecvx_lp_handler(amount, token: str, __: str, block: int) -> RewardsList:
    snapshot = sett_snapshot(Network.Ethereum, block, addresses.BVECVX_CVX_LP_SETT)
    return distribute_rewards_from_total_snapshot(
        amount,
        snapshot,
        token,
        block
    )


def ibbtc_peak_handler(amount: Decimal, token: str, sett: str, block: int) -> RewardsList:
    console.log(f"Distributing {amount} of {token} to ibbtc multisig")
    rewards = RewardsList()
    rewards.increase_user_rewards(addresses.IBBTC_MULTISIG, token, amount)
    return rewards


def treasury_handler(amount: Decimal, token: str, sett: str, block: int) -> RewardsList:
    console.log(f"Distributing {amount} of {token} to treasury multisig")
    rewards = RewardsList()
    rewards.increase_user_rewards(addresses.TREASURY_OPS, token, amount)
    return rewards


def fuse_pool_handler(amount: Decimal, token: str, sett: str, block: int) -> RewardsList:
    """
    Redirect rewards from rari pool contract to token holders in pool
    """
    snapshot = fuse_snapshot_of_token(Network.Ethereum, block, sett)
    return distribute_rewards_from_total_snapshot(amount, snapshot, token, block)
