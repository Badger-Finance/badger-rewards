from rewards.classes.RewardsList import RewardsList
from rewards.utils.rewards_utils import merkle_tree_to_rewards_list
import config.constants.addresses as addresses

def move_bvecvx(tree, tree_manager) -> RewardsList:
    BVECVX_AMOUNT = 3012474788017670000000

    rewards_list = merkle_tree_to_rewards_list(tree)

    rewards_list.increase_user_rewards(
        addresses.TREASURY_OPS,
        addresses.BVECVX,
        BVECVX_AMOUNT
    )
    return rewards_list
