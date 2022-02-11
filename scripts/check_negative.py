import json

from config.constants.addresses import DIGG
from helpers.digg_utils import digg_utils
from helpers.enums import Network
from rewards.snapshot.claims_snapshot import claims_snapshot
from subgraph.queries.setts import last_synced_block

if __name__ == "__main__":
    chain = Network.Ethereum
    diff_data = json.load(open("diff_data.json"))
    sum_negative = {}
    for user, token_data in diff_data["userTokenDiffs"].items():
        for token, amount in token_data.items():
            if amount < 0:
                if token in sum_negative:
                    sum_negative[token] += amount
                else:
                    sum_negative[token] = amount
    
    with open("negative_balances.json", "w") as fp2:
        json.dump(sum_negative, fp2)

