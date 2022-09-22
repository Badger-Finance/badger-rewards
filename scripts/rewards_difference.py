import json
import sys

from helpers.enums import Network
from logging_utils.logger import exception_logging
from rewards.aws.boost import download_boosts
from rewards.calc_rewards import generate_rewards_in_range
from rewards.utils.rewards_utils import get_cumulative_claimable_for_token
from scripts.rewards.utils.managers import get_tree_manager

sys.excepthook = exception_logging


if __name__ == "__main__":
    chain = Network.Ethereum
    diff_data = {"totalTokenDiffs": {}, "userTokenDiffs": {}}
    old_tree = json.load(open("old_tree.json"))

    broken_tree = json.load(open("current_tree.json"))

    start_block = int(old_tree["endBlock"])
    end_block = int(broken_tree["endBlock"])
    rewards_data = generate_rewards_in_range(
        chain,
        start_block,
        end_block,
        save=True,
        past_tree=old_tree,
        tree_manager=get_tree_manager(chain),
        boosts=download_boosts(chain),
    )
    fixed_tree = rewards_data["merkleTree"]

    for token, amount in broken_tree["tokenTotals"].items():
        total_token_fixed = fixed_tree["tokenTotals"][token]
        diff = amount - total_token_fixed
        diff_data["totalTokenDiffs"][token] = diff

    for user, claim in broken_tree["claims"].items():
        fixed_claim = fixed_tree["claims"][user]
        for token in claim["tokens"]:
            broken_cumulative_amount = get_cumulative_claimable_for_token(claim, token)
            fixed_cumulative_amount = get_cumulative_claimable_for_token(
                fixed_claim, token
            )
            diff = broken_cumulative_amount - fixed_cumulative_amount
            if user not in diff_data["userTokenDiffs"]:
                diff_data["userTokenDiffs"][user] = {}

            diff_data["userTokenDiffs"][user][token] = diff

    with open("diff_data.json", "w") as fp:
        json.dump(diff_data, fp)
