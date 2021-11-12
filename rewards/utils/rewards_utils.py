from rewards.classes.Snapshot import Snapshot
from rich.console import Console
from rewards.classes.RewardsList import RewardsList
from web3 import Web3
from typing import List, Dict, Callable

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


def distribute_rewards_to_snapshot(
    amount: float,
    snapshot: Snapshot,
    token: str,
    custom_rewards: Dict[str, Callable] = {},
):
    """
    Distribute a certain amount of rewards to a snapshot of users
    """
    rewards = RewardsList()
    custom_rewards_list = []
    total = snapshot.total_balance()
    if total == 0:
        unit = 0
    else:
        unit = amount / total
    for addr, balance in snapshot:
        reward_amount = balance * unit
        assert reward_amount >= 0
        if addr in custom_rewards:
            console.log(addr)
            custom_rewards_calc = custom_rewards[addr]
            console.log(token, amount, snapshot.token)
            custom_rewards_list.append(
                custom_rewards_calc(amount, token, snapshot.token)
            )
        else:
            rewards.increase_user_rewards(addr, token, int(reward_amount))
    return combine_rewards([rewards] + custom_rewards_list, 0)
