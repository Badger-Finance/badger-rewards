import config.constants.addresses as addresses
from rewards.classes.RewardsList import RewardsList
from rewards.utils.rewards_utils import get_cumulative_claimable_for_token
from rewards.utils.rewards_utils import merkle_tree_to_rewards_list

BCVXCRV_AMOUNT = 8043749707633587068811
GRAVIAURA_AMOUNT = 64711263876046333872


def redirect_rewards_func(tree, tree_manager) -> RewardsList:

    rewards_list = merkle_tree_to_rewards_list(tree)
    rewards_list.decrease_user_rewards(
        addresses.BVECVX_VOTER,
        addresses.BCVXCRV,
        BCVXCRV_AMOUNT
    )
    rewards_list.decrease_user_rewards(
        addresses.BVECVX_VOTER,
        addresses.GRAVIAURA,
        GRAVIAURA_AMOUNT
    )

    rewards_list.increase_user_rewards(
        addresses.TREASURY_OPS,
        addresses.BCVXCRV,
        BCVXCRV_AMOUNT
    )
    rewards_list.increase_user_rewards(
        addresses.TREASURY_OPS,
        addresses.GRAVIAURA,
        GRAVIAURA_AMOUNT
    )
    return rewards_list


def redirect_rewards_test(old_tree, new_tree) -> bool:
    old_claimable = old_tree["claims"][addresses.TREASURY_OPS]
    new_claimable = new_tree["claims"][addresses.TREASURY_OPS]
    old_bcvxcrv_claimable = get_cumulative_claimable_for_token(old_claimable, addresses.BCVXCRV)
    new_bcvxcrv_claimable = get_cumulative_claimable_for_token(new_claimable, addresses.BCVXCRV)
    bcvxcrv_diff = new_bcvxcrv_claimable - old_bcvxcrv_claimable
    old_gravi_claimable = get_cumulative_claimable_for_token(old_claimable, addresses.GRAVIAURA)
    new_gravi_claimable = get_cumulative_claimable_for_token(new_claimable, addresses.GRAVIAURA)
    gravi_diff = new_gravi_claimable - old_gravi_claimable
    # Checking Voter msig balances
    new_claimable_for_voter = new_tree["claims"][addresses.BVECVX_VOTER]
    new_bcvxcrv_claimable_voter = get_cumulative_claimable_for_token(
        new_claimable_for_voter, addresses.BCVXCRV
    )
    new_gravi_claimable_voter = get_cumulative_claimable_for_token(
        new_claimable_for_voter, addresses.BCVXCRV
    )
    return (bcvxcrv_diff == BCVXCRV_AMOUNT
            and gravi_diff == GRAVIAURA_AMOUNT
            and new_bcvxcrv_claimable_voter == 0
            and new_gravi_claimable_voter == 0)
