from helpers.constants import SETTS
from helpers.enums import Network
from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.utils.rewards_utils import distribute_rewards_to_snapshot


def eth_tree_handler(amount: float, token: str, sett: str):
    claims = claims_snapshot(Network.Ethereum)
    BCVXCRV = SETTS[Network.Ethereum]["bcvx_crv"]
    BVECVX = SETTS[Network.Ethereum]["bvecvx"]
    if sett in [BCVXCRV, BVECVX]:
        return distribute_rewards_to_snapshot(amount, claims[sett], token)
