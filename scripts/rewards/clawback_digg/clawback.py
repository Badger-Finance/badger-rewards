import config.constants.addresses as addresses
from typing import Dict
from rewards.classes.RewardsList import RewardsList
from rewards.utils.rewards_utils import (
    get_cumulative_claimable_for_token,
    merkle_tree_to_rewards_list
)


def get_dropt_claims(all_claims) -> Dict:
    claims = {}
    for user_claim in all_claims:
        cbs = user_claim["claimableBalances"]
        for cb in cbs:
            if cb["address"] == addresses.DROPT3:
                balance = int(cb["balance"])
                if balance > 0:
                    claims[user_claim["address"]] = balance
    print(claims)
    return claims


def clawback_func(tree, tree_manager) -> RewardsList:
    rewards_list = merkle_tree_to_rewards_list(tree)
    tree_dropt_balance = 34380917097829000000000
    trops_claimable = 33133901437149000000000

    rewards_list.increase_user_rewards(
        addresses.TREASURY_OPS, addresses.DROPT3, tree_dropt_balance - trops_claimable
    )
    return rewards_list


def clawback_test(old_tree, new_tree) -> bool:
    before_trops = get_cumulative_claimable_for_token(
        old_tree["claims"][addresses.TREASURY_OPS],
        addresses.DROPT3
    )
    after_trops = get_cumulative_claimable_for_token(
        new_tree["claims"][addresses.TREASURY_OPS],
        addresses.DROPT3
    )
    return after_trops > before_trops
