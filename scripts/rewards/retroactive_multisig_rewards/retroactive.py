from rewards.utils.rewards_utils import (
    get_cumulative_claimable_for_token,
    merkle_tree_to_rewards_list
)
import config.constants.addresses as addresses
addresses_to_move = [
    addresses.DEV_MULTISIG,
    addresses.TECH_OPS,
    addresses.TEST_MULTISIG,
    addresses.BADGER_PAYMENTS,
    addresses.OPS_MULTISIG_OLD,
    addresses.TREASURY_VAULT
]


def retroactive_func(tree, tree_manager):
    rewards_list = merkle_tree_to_rewards_list(tree)
    for addr in addresses_to_move:
        if addr in tree["claims"]:
            move_claim = tree["claims"][addr]
            claimed_for = tree_manager.get_claimed_for(addr, move_claim["tokens"])
            cumulative_claimable = dict(zip(move_claim["tokens"], move_claim["cumulativeAmounts"]))
            for token in move_claim["tokens"]:
                cumulative_claimable_amount = int(cumulative_claimable.get(token, 0))
                move_claimable = cumulative_claimable_amount - int(claimed_for.get(token, 0))
                rewards_list.increase_user_rewards(addresses.TREASURY_OPS, token, move_claimable)
                rewards_list.decrease_user_rewards(addr, token, move_claimable)

    return rewards_list


def test_retroactive_func(old_tree, new_tree):
    change_amount = {}
    for addr in addresses_to_move:
        for token in old_tree["tokenTotals"]:
            if addr in old_tree["claims"]:
                before = get_cumulative_claimable_for_token(old_tree["claims"][addr], token)
                after = get_cumulative_claimable_for_token(new_tree["claims"][addr], token)
            change_amount[token] = change_amount.get(token, 0) + after - before
    for token in change_amount.keys():
        if change_amount[token] > 0:
            return False
    return True
