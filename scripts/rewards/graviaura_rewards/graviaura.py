from config.constants.addresses import BADGER, GRAVIAURA
from helpers.enums import Network
from rewards.aws.boost import download_boosts
from rewards.calc_rewards import fetch_all_schedules
from rewards.classes.RewardsList import RewardsList
from rewards.classes.RewardsManager import RewardsManager
from rewards.classes.TreeManager import TreeManager
from rewards.utils.rewards_utils import combine_rewards, merkle_tree_to_rewards_list

START = 14973719
# First graviaura deposit
END = 14987641
# block when graviaura rewards resumed


def graviaura(tree, tree_manager: TreeManager) -> RewardsList:
    chain = Network.Ethereum
    rewards_list = merkle_tree_to_rewards_list(tree)
    boosts = download_boosts(chain)
    rewards_manager = RewardsManager(
        chain, tree_manager.next_cycle, START, END, boosts
    )
    schedules, _ = fetch_all_schedules(chain, START, END)
    graviaura_schedules = schedules[GRAVIAURA]
    # Calculate graviaura rewards from START to END
    sett_rewards, _, _, _ = rewards_manager.calculate_sett_rewards(
        GRAVIAURA,
        graviaura_schedules
    )
    return combine_rewards([rewards_list, sett_rewards], tree_manager.get_current_cycle())


def graviaura_test(old_tree, new_tree) -> bool:
    before_badger_total = old_tree["tokenTotals"][BADGER]
    after_badger_total = new_tree["tokenTotals"][BADGER]
    return after_badger_total > before_badger_total
