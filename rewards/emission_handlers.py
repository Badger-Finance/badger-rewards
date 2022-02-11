from decimal import Decimal

from rich.console import Console

from config.constants.addresses import IBBTC_MULTISIG
from config.constants.chain_mappings import UNCLAIMED_REWARDS_TOKENS
from helpers.enums import Network
from rewards.classes.RewardsList import RewardsList
from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.utils.rewards_utils import distribute_rewards_from_total_snapshot

console = Console()


def unclaimed_rewards_handler(amount: Decimal, token: str, sett: str, block: int):
    console.log("Distributing {} of {} to unclaimed rewards".format(amount, token))
    claimable = claims_snapshot(Network.Ethereum, block)
    if sett not in claimable:
        return RewardsList()
    if sett in UNCLAIMED_REWARDS_TOKENS[Network.Ethereum]:
        return distribute_rewards_from_total_snapshot(amount, claimable[sett], token, block)


def ibbtc_peak_handler(amount: Decimal, token: str, sett: str, block: int) -> RewardsList:
    console.log("Distributing {} of {} to ibbtc multisig".format(amount, token))
    rewards = RewardsList()
    rewards.increase_user_rewards(IBBTC_MULTISIG, token, amount)
    return rewards
