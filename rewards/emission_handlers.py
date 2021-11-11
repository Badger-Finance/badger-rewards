
from helpers.constants import BCVX, BCVXCRV
from helpers.enums import Network
from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.utils.rewards_utils import distribute_rewards_to_snapshot


def eth_tree_handler(amount, token, sett):
    claims = claims_snapshot(Network.Ethereum)
    if sett in [BCVX, BCVXCRV]:
        return distribute_rewards_to_snapshot(
            amount,
            claims[sett],
            token
        )
