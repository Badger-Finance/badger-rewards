from config.env_config import env_config
from rewards.classes.TreeManager import TreeManager
from couple import config
from rewards.aws.helpers import get_secret
from eth_account import Account
from scripts.rewards.eth.retroactive.fix_eth_rewards.fix_eth_rewards import fix_eth_rewards


if __name__ == "__main__":
    chain = "eth"
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    cycle_account = Account.from_key(cycle_key)

    tree_manager = TreeManager(chain, cycle_account)
    rewards = fix_eth_rewards()
    #tx_hash, propose_success = tree_manager.propose_root(rewards)
