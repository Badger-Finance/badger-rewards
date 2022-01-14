import json
import time

from decouple import config
from eth_account import Account

from config.singletons import env_config
from helpers.enums import Network
from rewards.aws.helpers import get_secret
from rewards.aws.trees import download_latest_tree
from rewards.calc_rewards import approve_root, propose_root
from rewards.classes.TreeManager import TreeManager
from subgraph.queries.setts import last_synced_block

if __name__ == "__main__":
    chain = Network.Ethereum
    tree = download_latest_tree(chain)
    key_decrypt_password = get_secret(
        "DECRYPT_PASSWORD_ARN",
        "DECRYPT_PASSWORD_KEY",
        region_name="us-west-2",
        kube=False,
    )
    with open(config("KEYFILE")) as key_file:
        key_file_json = json.load(key_file)
    cycle_key = Account.decrypt(key_file_json, key_decrypt_password)

    approve_tree_manager = TreeManager(chain, Account.from_key(cycle_key))

    end_block = approve_tree_manager.last_propose_end_block()
    start_block = int(tree["endBlock"]) + 1

    approve_root(chain, start_block, end_block, tree, approve_tree_manager)
