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


def fix_cycle(chain):
    tree = download_latest_tree(chain)
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )

    tree_manager = TreeManager(chain, Account.from_key(cycle_key))

    end_block = last_synced_block(chain)
    start_block = int(tree["endBlock"]) + 1

    propose_root(chain, start_block, end_block, tree, tree_manager)
    time.sleep(10)
    approve_root(chain, start_block, end_block, tree, tree_manager)
