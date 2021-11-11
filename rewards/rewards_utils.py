from rich.console import Console
from rewards.classes.RewardsList import RewardsList
from web3 import Web3
from typing import List

console = Console()


def get_cumulative_claimable_for_token(claim, token: str):
    tokens = claim["tokens"]
    amounts = claim["cumulativeAmounts"]

    console.log(tokens, amounts)

    for i in range(len(tokens)):
        address = tokens[i]
        if token == address:
            return int(amounts[i])

    # If address was not found
    return 0


def get_claimed_for_token(data, token: str) -> int:
    tokens = data[0]
    amounts = data[1]

    for i in range(len(tokens)):
        address = tokens[i]
        if token == address:
            return amounts[i]


def keccak(value: str):
    return Web3.toHex(Web3.keccak(text=value))


def combine_rewards(rewards_list: List[RewardsList], cycle):
    combined_rewards = RewardsList(cycle)
    for rewards in rewards_list:
        for user, claims in rewards.claims.items():
            for token, claim in claims.items():
                combined_rewards.increase_user_rewards(user, token, claim)
    return combined_rewards


def process_cumulative_rewards(current, new: RewardsList) -> RewardsList:
    """Combine past rewards with new rewards

    :param current: current rewards
    :param new: new rewards
    """
    result = RewardsList(new.cycle)

    # Add new rewards
    for user, claims in new.claims.items():
        for token, claim in claims.items():
            result.increase_user_rewards(user, token, claim)

    # Add existing rewards
    for user, user_data in current["claims"].items():
        for i in range(len(user_data["tokens"])):
            token = user_data["tokens"][i]
            amount = user_data["cumulativeAmounts"][i]
            result.increase_user_rewards(user, token, int(amount))

    # result.printState()
    return result


def merkle_tree_to_rewards_list(tree):
    return process_cumulative_rewards(tree, RewardsList(int(tree["cycle"])))
