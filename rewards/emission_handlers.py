from helpers.constants import IBBTC_MULTISIG, SETTS
from helpers.enums import Network
from rewards.classes.RewardsList import RewardsList
from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.utils.rewards_utils import distribute_rewards_to_snapshot


def unclaimed_rewards_handler(amount: float, token: str, sett: str, block: int):
    claimable = claims_snapshot(Network.Ethereum, block)
    BCVXCRV = SETTS[Network.Ethereum]["cvx_crv"]
    BVECVX = SETTS[Network.Ethereum]["bvecvx"]
    if sett in [BCVXCRV, BVECVX]:
        return distribute_rewards_to_snapshot(amount, claimable[sett], token)


def ibbtc_peak_handler(amount: float, token: str, sett: str) -> RewardsList:
    rewards = RewardsList()
    rewards.increase_user_rewards(IBBTC_MULTISIG, token, amount)
    return rewards

