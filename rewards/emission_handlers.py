from helpers.constants import SETTS
from helpers.enums import Network
from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.utils.rewards_utils import distribute_rewards_to_snapshot


def eth_tree_handler(amount: float, token: str, sett: str, block: int):
    claiamble = claims_snapshot(Network.Ethereum, block)
    BCVXCRV = SETTS[Network.Ethereum]["cvx_crv"]
    BVECVX = SETTS[Network.Ethereum]["bvecvx"]
    if sett in [BCVXCRV, BVECVX]:
        return distribute_rewards_to_snapshot(amount, claiamble[sett], token)
