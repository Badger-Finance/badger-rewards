from helpers.enums import Network
from rewards.aws.trees import download_latest_tree
from rewards.classes.TreeManager import TreeManager
from rewards.aws.helpers import get_secret
from config.env_config import env_config
from eth_account import Account
from rewards.calc_rewards import approve_root, propose_root
import time
from subgraph.queries.setts import last_synced_block
from decouple import config
from eth_account import Account
import json


def fix_cycle(chain):
    tree = download_latest_tree(chain)
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    if chain == Network.Ethereum:
        key_decrypt_password = get_secret(
            config("DECRYPT_PASSWORD_ARN"),
            config("DECRYPT_PASSWORD_KEY"),
            region_name="us-west-2",
        )
        with open(config("KEYFILE")) as key_file:
            key_file_json = json.load(key_file)
        cycle_key = Account.decrypt(key_file_json, key_decrypt_password)
        cycle_account = Account.from_key(cycle_key)
    else:
        cycle_account = Account.from_key(cycle_key)

    tree_manager = TreeManager(chain, cycle_account)
    end_block = last_synced_block(chain)
    start_block = int(tree["endBlock"]) + 1

    propose_root(chain, start_block, end_block, tree, tree_manager)
    time.sleep(10)
    approve_root(chain, start_block, end_block, tree, tree_manager)
