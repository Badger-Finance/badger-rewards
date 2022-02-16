import json

from eth_account import Account

from config.singletons import env_config
from helpers.enums import Network
from rewards.aws.helpers import get_secret
from rewards.calc_rewards import generate_rewards_in_range
from rewards.classes.TreeManager import TreeManager


if __name__ == "__main__":
    chain = Network.Ethereum
    tree_file_name = (
        "rewards-1-0x83b8544a0ea1cac9747c4aec3c9e6df79611bd6c1e54333d101ac162df82cd91.json"
    )
    tree = json.load(open(tree_file_name))
    start_block = int(tree["endBlock"]) + 1
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    cycle_account = Account.from_key(cycle_key)

    tree_manager = TreeManager(chain, cycle_account)
    end_block = 13373308
    tree_manager = TreeManager(chain, cycle_account)
    print(start_block, end_block)
    rewards = generate_rewards_in_range(
        chain,
        start=start_block,
        end=end_block,
        save=False,
        past_tree=tree,
        tree_manager=tree_manager,
    )
    tx_hash, propose_success = tree_manager.propose_root(rewards)
