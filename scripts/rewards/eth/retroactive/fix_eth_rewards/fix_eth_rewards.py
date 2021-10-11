
if __name__ == "__main__":
from rewards.aws.trees import upload_tree
from rewards.aws.boost import add_multipliers
from rewards.calc_rewards import generate_rewards_in_range
from config.env_config import env_config
from rewards.classes.TreeManager import TreeManager
from decouple import config
import json
from rewards.aws.helpers import get_secret
from eth_account import Account
from subgraph.queries.setts import last_synced_block


def fix_eth_rewards(): 
    chain = "eth"
    tree_file_name = "rewards-1-0xd00b9252eeb4b0a35a9e23b24f28a3154a09f1072f6b2f870796347eee844870.json"
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
    end_block = 13398599
    print(start_block, end_block)
    rewards = generate_rewards_in_range(
        chain,
        start=start_block,
        end=end_block,
        save=False,
        past_tree=tree,
        tree_manager=tree_manager,
    )
    return rewards
