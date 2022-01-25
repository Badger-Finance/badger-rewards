import json
from rewards.snapshot.chain_snapshot import sett_snapshot
from helpers.enums import Network
from rewards.utils.rewards_utils import distribute_rewards_to_snapshot, combine_rewards


def migration_rewards(tree, tree_manager):
    chain = Network.Ethereum
    rewards_list = merkle_tree_to_rewards_list(tree)
    new_rewards = []
    migrated_rewards = json.load(open("migration_rewards.json"))
    for harvest_data in migrated_rewards:
        block = int(harvest_data["block"])
        sett = harvest_data["sett"]
        token = harvest_data["token"]
        amount = harvest_data["amount"]
        snap = sett_snapshot(chain, block, sett, blacklist=True)
        new_rewards.append(
            distribute_rewards_to_snapshot(
                amount,
                snap,
                token,
                block,
            )
        )

    total_rewards = combine_rewards(
        [*new_rewards, rewards_list], rewards_list.cycle + 1
    )
    return total_rewards
    
