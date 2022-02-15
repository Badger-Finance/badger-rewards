from rewards.classes.RewardsList import RewardsList
from rewards.utils.rewards_utils import get_cumulative_claimable_for_token, merkle_tree_to_rewards_list
import config.constants.addresses as addresses

BVECVX_AMOUNT = 3012474788017670000000

def move_bvecvx_func(tree, tree_manager) -> RewardsList:

    rewards_list = merkle_tree_to_rewards_list(tree)

    rewards_list.increase_user_rewards(
        addresses.TREASURY_OPS,
        addresses.BVECVX,
        BVECVX_AMOUNT
    )
    return rewards_list

def move_bvecvx_test(old_tree, new_tree) -> bool:
    old_claimable = old_tree["claims"][addresses.TREASURY_OPS]
    new_claimable = new_tree["claims"][addresses.TREASURY_OPS]
    old_bvecvx_claimable = get_cumulative_claimable_for_token(old_claimable, addresses.BVECVX)
    new_bvecvx_claimable = get_cumulative_claimable_for_token(new_claimable, addresses.BVECVX)
    return new_bvecvx_claimable - old_bvecvx_claimable == BVECVX_AMOUNT



