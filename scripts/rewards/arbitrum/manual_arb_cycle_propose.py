import json

from eth_account import Account
from rich.console import Console

from config.singletons import env_config
from helpers.enums import Network
from rewards.aws.helpers import get_secret
from rewards.calc_rewards import propose_root
from rewards.classes.TreeManager import TreeManager
from scripts.rewards.utils.propose_rewards import propose_rewards

console = Console()

if __name__ == "__main__":
    chain = Network.Arbitrum
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    cycle_account = Account.from_key(cycle_key)

    tree_manager = TreeManager(chain, cycle_account)

    arb_tree = json.load(open("arb_tree.json"))
    start_block = arb_tree["endBlock"]
    end_block = 2403325

    propose_root(chain, start_block, end_block, arb_tree, tree_manager, save=True)
