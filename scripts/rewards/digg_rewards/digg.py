from config.constants.addresses import BSLP_DIGG_WBTC, DIGG
from helpers.enums import Network
from rewards.calc_rewards import fetch_all_schedules
from rewards.classes.RewardsList import RewardsList
from rewards.classes.RewardsManager import RewardsManager
from rewards.classes.TreeManager import TreeManager
from rewards.utils.rewards_utils import combine_rewards, merkle_tree_to_rewards_list

START = 14886049
# Start block of cycle when digg emissions stopped


def digg(tree, tree_manager: TreeManager) -> RewardsList:
    chain = Network.Ethereum
    rewards_list = merkle_tree_to_rewards_list(tree)
    current_tree = tree_manager.fetch_current_tree()
    end_block = int(current_tree["endBlock"])
    boosts = {"userData": {}}
    # Boosts not needed since distributing rewards to non boosted sett
    rewards_manager = RewardsManager(
        chain, tree_manager.next_cycle, START, end_block, boosts
    )
    schedules, _ = fetch_all_schedules(chain, START, end_block)
    digg_schedules = schedules[BSLP_DIGG_WBTC]
    # Calculate digg rewards from START to now
    sett_rewards, _, _, _ = rewards_manager.calculate_sett_rewards(
        BSLP_DIGG_WBTC,
        digg_schedules
    )
    return combine_rewards([rewards_list, sett_rewards], tree_manager.get_current_cycle())


def digg_test(old_tree, new_tree) -> bool:
    before_digg_total = old_tree["tokenTotals"][DIGG]
    after_digg_total = new_tree["tokenTotals"][DIGG]
    return after_digg_total > before_digg_total
