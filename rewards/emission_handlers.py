from helpers.constants import SETTS
from helpers.enums import Network
from rewards.snapshot.chain_snapshot import sett_snapshot
from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.utils.rewards_utils import distribute_rewards_to_snapshot


def eth_tree_handler(amount: float, token: str, sett: str, block: int):
    claims = claims_snapshot(Network.Ethereum)
    BCVXCRV = SETTS[Network.Ethereum]["cvx_crv"]
    BVECVX = SETTS[Network.Ethereum]["bvecvx"]
    if sett in [BCVXCRV, BVECVX]:
        return distribute_rewards_to_snapshot(amount, claims[sett], token)

def bvecvx_lp_handler(amount, token: str, sett: str, block: int):
    bbvecvx_cvx_lp = SETTS[Network.Ethereum]["bvecvx_cvx"]
    snapshot = sett_snapshot(Network.Ethereum, block, bbvecvx_cvx_lp)
    return distribute_rewards_to_snapshot(
        amount,
        snapshot,
        token
    )
