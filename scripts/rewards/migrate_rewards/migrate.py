from helpers.enums import Network
from rewards.classes.RewardsList import RewardsList
import json
from rewards.snapshot.chain_snapshot import sett_snapshot
from scripts.rewards.migrate_rewards.calc_migration_data import harvests

from rewards.utils.rewards_utils import (
    combine_rewards,
    distribute_rewards_from_total_snapshot,
    merkle_tree_to_rewards_list
)


def migrate_func(tree, tree_manager) -> RewardsList:
    tree = merkle_tree_to_rewards_list(tree)
    migration_rewards = []
    for migration_harvest in harvests:
        vault = migration_harvest["sett"]
        block = migration_harvest["block"]
        amount = migration_harvest["amount"]
        snapshot = sett_snapshot(Network.Ethereum, block, vault)
        migration_rewards.append(distribute_rewards_from_total_snapshot(
            amount,
            snapshot,
            migration_harvest["token"],
            block
        ))
    return combine_rewards(migration_rewards, 0)


def migrate_test(old_tree, new_tree):
    token_agg = {}
    migration_data = json.load(open("migration_data.json"))
    for migration_harvest in migration_data:
        token = migration_harvest["token"]
        token_agg[token] = token_agg.get(token) + migration_harvest["amount"]

    for token, amount in old_tree["tokenTotals"].items():
        if not amount == new_tree["tokenTotals"][token] + token_agg[token]:
            return False
    return True
