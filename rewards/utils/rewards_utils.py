from decimal import Decimal
from typing import Callable, Dict, List, Optional

from rich.console import Console
from web3 import Web3

from config.constants.emissions import ZERO_CYCLE
from rewards.classes.RewardsList import RewardsList
from rewards.classes.Snapshot import Snapshot

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


def distribute_rewards_to_snapshot(
    amount: float,
    snapshot: Snapshot,
    token: str,
    block: int,
    custom_rewards: Dict[str, Callable] = {},
) -> RewardsList:
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
        reward_amount = Decimal(balance) * unit
        assert reward_amount >= 0
        if addr in custom_rewards:
            custom_rewards_calc = custom_rewards[addr]
            custom_rewards_list.append(
                custom_rewards_calc(reward_amount, token, snapshot.token, block)
            )
        else:
            rewards.increase_user_rewards(addr, token, reward_amount)
    return combine_rewards([rewards] + custom_rewards_list, 0)


def distribute_rewards_from_total_snapshot(
        amount: int, snapshot: Snapshot, token: str,
        block: int, custom_rewards: Optional[Dict[str, Callable]] = None,
):
    if not custom_rewards:
        custom_rewards = {}
    rewards = RewardsList()
    custom_rewards_list = []
    total = snapshot.total_balance()
    # TODO: Think about refactoring this and splitting it into two separate funcs:
    # TODO: one for normal rewards another for custom rewards
    for addr, balance in snapshot:
        rewards_percentage = Decimal(balance) / total if not total == 0 else 0
        reward_amount = Decimal(amount) * rewards_percentage
        assert reward_amount >= 0
        if addr in custom_rewards:
            custom_rewards_calc = custom_rewards[addr]
            console.log(token, amount, snapshot.token)
            custom_rewards_list.append(
                custom_rewards_calc(reward_amount, token, snapshot.token, block)
            )
        else:
            rewards.increase_user_rewards(addr, token, reward_amount)
    return combine_rewards([rewards] + custom_rewards_list, ZERO_CYCLE)


def process_cumulative_rewards(current, new: RewardsList) -> RewardsList:
    """Combine past rewards with new rewards

    :param current: current rewards
    :param new: new rewards
    """
    result = RewardsList(new.cycle)

    # Add new rewards
    for user, claims in new.claims.items():
        for token, claim in claims.items():
            result.increase_user_rewards(user, token, Decimal(claim))

    # Add existing rewards
    for user, user_data in current["claims"].items():
        for i in range(len(user_data["tokens"])):
            token = user_data["tokens"][i]
            amount = user_data["cumulativeAmounts"][i]
            result.increase_user_rewards(user, token, Decimal(amount))
    return result


def merkle_tree_to_rewards_list(tree):
    return process_cumulative_rewards(tree, RewardsList(int(tree["cycle"])))
