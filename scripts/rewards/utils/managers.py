from eth_account import Account
from rewards.aws.helpers import get_secret
from rewards.classes.TreeManager import TreeManager
from config.singletons import env_config


def get_tree_manager(chain: str):
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    cycle_account = Account.from_key(cycle_key)

    return TreeManager(chain, cycle_account)
