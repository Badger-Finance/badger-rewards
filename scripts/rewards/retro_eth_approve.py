from rewards.aws.trees import upload_tree
from rewards.aws.boost import add_multipliers
from rewards.calc_rewards import generate_rewards_in_range

from rewards.classes.TreeManager import TreeManager
from decouple import config
import json
from rewards.aws.helpers import get_secret
from eth_account import Account
from subgraph.queries.setts import last_synced_block


if __name__ == "__main__":
    chain = "eth"
    tree_file_name = "rewards-1-0x83b8544a0ea1cac9747c4aec3c9e6df79611bd6c1e54333d101ac162df82cd91.json"
    tree = json.load(open(tree_file_name))
    start_block = tree["endBlock"] + 1
    
    with open(config("KEYFILE")) as key_file:
        key_file_json = json.load(key_file)
        
    key_decrypt_password = get_secret(
        config("DECRYPT_PASSWORD_ARN"),
        config("DECRYPT_PASSWORD_KEY"),
        region_name="us-west-2",
    )
    cycle_key = Account.decrypt(key_file_json, key_decrypt_password)
    cycle_account = Account.from_key(cycle_key)
    end_block = 13373308
    tree_manager = TreeManager(chain, cycle_account)
    print(start_block, end_block)
    rewards = generate_rewards_in_range(
        chain,
        start=start_block,
        end=end_block,
        save=False,
        past_tree=tree,
        tree_manager=tree_manager
    )
    tx_hash, approve_success = tree_manager.approve_root(
        rewards
    )
    if approve_success:
        upload_tree(
            rewards["fileName"],
            rewards["merkleTree"],
            chain,
            False
        )
        add_multipliers(
            rewards["multiplierData"], rewards["userMultipliers"]
        )



    
    
    
    