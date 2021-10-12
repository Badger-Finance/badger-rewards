from rewards.aws.trees import upload_tree
from rewards.aws.boost import add_multipliers
from rewards.classes.TreeManager import TreeManager
from decouple import config
import json
from rewards.aws.helpers import get_secret
from eth_account import Account
from scripts.rewards.eth.retroactive.fix_eth_rewards.fix_eth_rewards import (
    fix_eth_rewards,
)

if __name__ == "__main__":
    chain = "eth"
    with open(config("KEYFILE")) as key_file:
        key_file_json = json.load(key_file)

    key_decrypt_password = get_secret(
        config("DECRYPT_PASSWORD_ARN"),
        config("DECRYPT_PASSWORD_KEY"),
        region_name="us-west-2",
    )
    cycle_key = Account.decrypt(key_file_json, key_decrypt_password)
    cycle_account = Account.from_key(cycle_key)
    tree_manager = TreeManager(chain, cycle_account)

    rewards = fix_eth_rewards(tree_manager)
  