import json

from config.constants.addresses import DIGG
from helpers.digg_utils import DiggUtils
from helpers.enums import Network
from rewards.snapshot.claims_snapshot import claims_snapshot
from subgraph.queries.setts import last_synced_block

if __name__ == "__main__":
    digg_utils = DiggUtils()
    chain = Network.Ethereum
    claimable = claims_snapshot(chain, last_synced_block(chain))
    diff_data = json.load(open("diff_data.json"))
    user_reduction_data = {}
    rewards_left = {}
    for user, token_data in diff_data["userTokenDiffs"].items():
        for token, amount in token_data.items():
            if user in claimable[token].balances:
                if token == DIGG:
                    claimable_bal = digg_utils.fragments_to_shares(
                        float(claimable[token].balances[user]) * 1e9
                    )
                else:
                    claimable_bal = float(claimable[token].balances[user]) * 1e18
            else:
                claimable_bal = 0

            if user not in user_reduction_data:
                user_reduction_data[user] = {}
            # if the users debt is less than what is claimable pay back the debt
            if amount <= claimable_bal:
                user_reduction_data[user][token] = amount
            else:
                # Otherwise, just pay back what is claimable
                if user not in rewards_left:
                    rewards_left[user] = {}
                rewards_left[user][token] = amount - claimable_bal
                user_reduction_data[user][token] = claimable_bal
    with open("balance_changes.json", "w") as fp:
        json.dump(user_reduction_data, fp)
    with open("debt_left.json", "w") as fp2:
        json.dump(rewards_left, fp2)

    sum_token_debt = {}
    for user, data in rewards_left.items():
        for token, amount in data.items():
            if token == DIGG:
                amount = digg_utils.shares_to_fragments(amount)
            if token not in sum_token_debt:
                sum_token_debt[token] = 0
            sum_token_debt[token] += amount
