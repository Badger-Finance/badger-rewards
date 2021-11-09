
from helpers.constants import BCVX, BCVXCRV
from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.utils.rewards_utils import distribute_rewards_to_snapshot


def tree_handler(amount, token, sett):
    claims = claims_snapshot()
    if sett in [BCVX, BCVXCRV]:
        return distribute_rewards_to_snapshot(
            amount,
            claims[sett],
            token
        )
