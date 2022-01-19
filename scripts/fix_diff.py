import json
from helpers.enums import Network
from subgraph.queries.setts import last_synced_block
from rewards.snapshot.claims_snapshot import claims_snapshot

if __name__ == "__main__":
    chain = Network.Ethereum
    claimable = claims_snapshot(chain, last_synced_block(chain))
    diff_data = json.load(open("diff_data.json"))
    user_reduction_data = {}
    rewards_left = {}
    for user, token_data in diff_data["userTokenDiffs"].items():
        for token, amount in token_data.items():
            if amount > 0 and user in claimable[token].balances:
                if user not in user_reduction_data:
                    user_reduction_data[user] = {}
                reduced = amount - claimable[token][user]
                # if the users debt is less than what is claimable pay back the debt
                if amount <= claimable[token][user]:
                    user_reduction_data[user][token] = amount
                else:
                    # Otherwise, just pay back what is claimable
                    if user not in rewards_left:
                        rewards_left[user] = {}
                    rewards_left[user] = amount - claimable[user][token]
                    user_reduction_data[data][token] = claimable[user][token]
    with open("balance_changes.json", "w") as fp:
        json.dump(user_reduction_data, fp)
    with open("debt_left.json", "w") as fp2:
        json.dump(rewards_left, fp2)

    sum_token_debt = {}
    for user, data in reward_left.items():
        for token, amount in data.items():
            if token not in sum_token_debt:
                sum_token_debt[token] = 0
            sum_token_debt[token] += amount

    print(sum_token_debt)
