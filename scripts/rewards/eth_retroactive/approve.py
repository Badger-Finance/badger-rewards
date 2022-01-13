import json
import time

from decouple import config
from eth_account import Account

from config.singletons import env_config
from helpers.enums import Network
from rewards.aws.helpers import get_secret
from rewards.aws.trees import download_latest_tree, upload_tree
from rewards.classes.TreeManager import TreeManager
from scripts.rewards.eth_retroactive.retro import retro_cycle

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
    rewards_data = retro_cycle(tree, approve_tree_manager)
    tx_hash, succeded = approve_tree_manager.approve_root(rewards_data)
    if succeded:
        upload_tree(
            rewards_data["fileName"],
            rewards_data["merkleTree"],
            chain,
            staging=env_config.test or env_config.staging,
        )
