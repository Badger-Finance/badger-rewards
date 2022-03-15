from helpers.enums import Network
from rewards.classes.RewardsList import RewardsList
from rewards.snapshot.chain_snapshot import sett_snapshot
from scripts.rewards.migrate_rewards.calc_migration_data import harvests

from rewards.utils.rewards_utils import (
    combine_rewards,
    distribute_rewards_from_total_snapshot,
    merkle_tree_to_rewards_list
)


def migrate_func(tree, tree_manager) -> RewardsList:
    rewards_list = merkle_tree_to_rewards_list(tree)
    migration_rewards = []
    for migration_harvest in harvests:
        vault = migration_harvest["sett"]
        block = migration_harvest["block"]
        amount = migration_harvest["amount"]
        snapshot = sett_snapshot(Network.Ethereum, block, vault)
        migration_rewards.append(distribute_rewards_from_total_snapshot(
            int(amount),
            snapshot,
            migration_harvest["token"],
            block
        ))
    
    return combine_rewards([*migration_rewards, rewards_list], 0)


def migrate_test(old_tree, new_tree):
    token_agg = {}
    for migration_harvest in harvests:
        token = migration_harvest["token"]
        token_agg[token] = token_agg.get(token, 0) + int(migration_harvest["amount"])

    for token, amount in old_tree["tokenTotals"].items():
        new_amount = new_tree["tokenTotals"][token] + token_agg.get(token, 0)
        if amount != new_amount:
            return False
    return True
