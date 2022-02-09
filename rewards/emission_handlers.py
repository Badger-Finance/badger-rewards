from decimal import Decimal
from rich.console import Console

from config.constants.addresses import IBBTC_MULTISIG
from config.constants.chain_mappings import UNCLAIMED_REWARDS_TOKENS
from helpers.enums import Network
from rewards.classes.RewardsList import RewardsList
from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.snapshot.chain_snapshot import sett_snapshot
from rewards.snapshot.token_snapshot import fuse_snapshot_of_token
from rewards.utils.rewards_utils import distribute_rewards_from_total_snapshot

console = Console()


def unclaimed_rewards_handler(amount: Decimal, token: str, sett: str, block: int) -> RewardsList:
    """
    Redirect rewards from badger tree to users with unclaimed rewards
    """
    console.log("Distributing {} of {} to unclaimed rewards".format(amount, token))
    claimable = claims_snapshot(Network.Ethereum, block)
    if sett not in claimable:
        return RewardsList()
    if sett in UNCLAIMED_REWARDS_TOKENS[Network.Ethereum]:
        return distribute_rewards_from_total_snapshot(amount, claimable[sett], token, block)


def ibbtc_peak_handler(amount: Decimal, token: str, sett: str, block: int) -> RewardsList:
    """
    Redirect rewards from ibbtc contract to ibbtc multisig"
    """
    console.log("Distributing {} of {} to ibbtc multisig".format(amount, token))
    rewards = RewardsList()
    rewards.increase_user_rewards(IBBTC_MULTISIG, token, amount)
    return rewards


def rari_pool_handler(amount: Decimal, token: str, sett: str, block: int) -> RewardsList:
    """ 
    Redirect rewards from rari pool contract to token holders in pool
    """
    snapshot = fuse_snapshot_of_token(Network.Ethereum, block, sett)
    return distribute_rewards_from_total_snapshot(amount, snapshot, token, block)