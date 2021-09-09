import json
from helpers.constants import TOKENS_TO_CHECK
from tabulate import tabulate
from rich.console import Console

console = Console()
def assert_claims_increase(past_tree, new_tree):
    # Each users cumulative claims must only increase
    past_claims = past_tree["claims"]
    new_claims = new_tree["claims"]
    
    for user, past_claim in past_claims.items():
        if user in new_claims:
            new_claim  = new_claims[user]
            for past_token in past_claim["tokens"]:
                past_cumulative_amounts = past_claim["cumulativeAmounts"]
                new_cumulative_amounts = new_claim["cumulativeAmounts"]
                past_amount = past_cumulative_amounts[past_claim["tokens"].index(past_token)]
                new_amount = new_cumulative_amounts[new_claim["tokens"].index(past_token)]
                diff = new_amount - past_amount
                console.log(past_token, new_amount, past_amount )  
                assert diff >= 0
                
def val(amount, decimals=18):
    return "{:,.18f}".format(amount / 10 ** decimals)

def print_token_diff_table(name, before, after, sanity_diff, decimals=18):
    diff = after - before

    console.print("Diff for {}".format(name))
    table = []
    table.append(["{} before".format(name), val(before, decimals=decimals)])
    table.append(["{} after".format(name), val(after, decimals=decimals)])
    table.append(["{} diff".format(name), val(diff, decimals=decimals)])
    print(tabulate(table, headers=["key", "value"]))

    assert diff <= sanity_diff

def verify_rewards(past_tree, new_tree):
    console.log("Verifying Rewards ...")
    assert_claims_increase(past_tree, new_tree)
    for name, token in TOKENS_TO_CHECK.items():
        if name in ["Digg"]:
            continue
        total_before_token = int(past_tree["tokenTotals"].get(token, 0))
        total_after_token = int(new_tree["tokenTotals"].get(token, 0))
        print_token_diff_table(
            name, total_before_token, total_after_token, 40000 * 1e18
        )
    