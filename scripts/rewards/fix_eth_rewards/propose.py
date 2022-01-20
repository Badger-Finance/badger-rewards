from eth_account import Account

from config.singletons import env_config
from helpers.enums import Network
from rewards.aws.helpers import get_secret
from rewards.aws.trees import download_latest_tree
from rewards.classes.TreeManager import TreeManager
from scripts.rewards.eth_retroactive.fix import fix

if __name__ == "__main__":
    chain = Network.Ethereum
    tree = download_latest_tree(chain)
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    propose_tree_manager = TreeManager(chain, Account.from_key(cycle_key))

    rewards_data = fix(tree, propose_tree_manager)
    tx_hash, succeded = propose_tree_manager.propose_root(rewards_data)
