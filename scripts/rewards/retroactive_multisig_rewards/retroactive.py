from rewards.utils.rewards_utils import merkle_tree_to_rewards_list
import config.constants.addresses as addresses

addresses_to_move = []


def retroactive_func(tree, tree_manager):
    rewards_list = merkle_tree_to_rewards_list(tree)
    for addr in addresses_to_move:
        move_claim = tree["claims"][addr]
        claimed_for = tree_manager.get_claimed_for(addr, move_claim["tokens"])
        cumulative_claimable = zip(move_claim["tokens"], move_claim["cumulativeAmounts"])
        for token in move_claim["tokens"]:
            move_claimable = cumulative_claimable.get(token, 0) - claimed_for.get(token, 0)
            rewards_list.increase_user_rewards(addresses.TREASURY_OPS, token, move_claimable)
            rewards_list.decrease_user_rewards(addr, token, move_claimable)

    return rewards_list


def test_retroactive_func(old_tree, new_tree):
    pass
