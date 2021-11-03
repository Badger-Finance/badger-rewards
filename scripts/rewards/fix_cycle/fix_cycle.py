from scripts.rewards.utils.approve_rewards import approve_rewards
from rewards.calc_rewards import generate_rewards_in_range
from rewards.classes.TreeManager import TreeManager
from rewards.tree_utils import get_last_proposed_cycle, calc_next_cycle_range
from rewards.aws.helpers import get_secret
from config.env_config import env_config
from helpers.constants import MONITORING_SECRET_NAMES
from eth_account import Account
from rewards.calc_rewards import approve_root, propose_root
import time
from scripts.rewards.utils.propose_rewards import propose_rewards
from subgraph.queries.setts import last_synced_block


def fix_cycle(chain, tree):
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    cycle_account = Account.from_key(cycle_key)
    tree_manager = TreeManager(chain, cycle_account)
    end_block = last_synced_block(chain)
    start_block = int(tree["endBlock"]) + 1

    propose_root(chain, start_block, end_block, tree, tree_manager)
    time.sleep(10)
    approve_root(chain, start_block, end_block, tree, tree_manager)
