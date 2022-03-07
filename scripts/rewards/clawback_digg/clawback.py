from badger_api.claimable import get_latest_claimable_snapshot
from helpers.enums import Network
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
                claims[user_claim["address"]] = int(cb["balance"])
    return claims


def clawback_func(tree, tree_manager) -> RewardsList:
    chain = Network.Ethereum
    rewards_list = merkle_tree_to_rewards_list(tree)
    dropt_claims = get_dropt_claims(get_latest_claimable_snapshot(chain))
    for addr, value in dropt_claims.items():
        rewards_list.increase_user_rewards(
            addresses.TREASURY_OPS, addresses.DROPT3, value
        )
        rewards_list.decrease_user_rewards(
            addr,
            addresses.DROPT3,
            value
        )
    return rewards_list


def clawback_test(old_tree, new_tree) -> bool:
    before_dropt3 = old_tree["tokenTotals"][addresses.DROPT3]
    after_dropt3 = new_tree["tokenTotals"][addresses.DROPT3]
    before_trops = get_cumulative_claimable_for_token(
        old_tree["claims"][addresses.TREASURY_OPS],
        addresses.DROPT3
    )
    after_trops = get_cumulative_claimable_for_token(
        new_tree["claims"][addresses.TREASURY_OPS],
        addresses.DROPT3
    )
    return before_dropt3 == after_dropt3 and after_trops > before_trops
