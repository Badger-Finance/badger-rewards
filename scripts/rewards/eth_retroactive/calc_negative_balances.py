import json

from helpers.constants import BADGER, DIGG
from helpers.enums import Network
from rewards.aws.trees import download_latest_tree
from scripts.rewards.utils.managers import get_tree_manager


def negative_balances(tree):
    chain = Network.Ethereum
    tree_manager = get_tree_manager(chain)
    tokens_to_check = [BADGER, DIGG]
    affected_users = {}
    for user, claim in tree["claims"].items():
        claimed = tree_manager.get_claimed_for(user, tokens_to_check)
        for token in tokens_to_check:
            if token in claim["tokens"]:
                claimed_token = int(claimed[1][claimed[0].index(token)])
                cumulativeAmount = int(claim["cumulativeAmounts"][claim["tokens"].index(token)])
                claimable_amount = int(cumulativeAmount) - int(claimed_token)
                if claimable_amount < 0:
                    if user not in affected_users:
                        affected_users[user] = {}
                    affected_users[user][token] = abs(claimable_amount)
    print(len(affected_users))
    with open("affected_users.json", "w") as fp:
        json.dump(affected_users, fp)

if __name__ == "__main__":
    tree = download_latest_tree(Network.Ethereum)
    negative_balances(tree)