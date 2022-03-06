from badger_api.claimable import get_latest_claimable_snapshot
from helpers.enums import Network
import config.constants.addresses as addresses

def get_dropt_claims(all_claims):
    pass


def clawback_func(tree, tree_manager):
    chain = Network.Ethereum
    dropt_claims = get_dropt_claims(get_latest_claimable_snapshot(chain))


    pass

def clawback_test(old_tree, new_tree):
    pass