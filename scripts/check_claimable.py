from scripts.rewards.utils.managers import get_tree_manager
from rewards.tree_utils import calc_claimable_balances
if __name__ == "__main__":
    tree_manager = get_tree_manager("eth")
    tree = tree_manager.fetch_current_tree()
    print(calc_claimable_balances(tree_manager, list(tree["tokenTotals"].keys()), tree))
