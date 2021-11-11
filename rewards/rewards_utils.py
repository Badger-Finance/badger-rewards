from rewards.classes.Snapshot import Snapshot
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


def combine_rewards(rewards_list: List[RewardsList], cycle) -> RewardsList:
    combined_rewards = RewardsList(cycle)
    for rewards in rewards_list:
        for user, claims in rewards.claims.items():
            for token, claim in claims.items():
                combined_rewards.increase_user_rewards(user, token, claim)
    return combined_rewards
