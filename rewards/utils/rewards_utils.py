from collections import defaultdict
from decimal import Decimal
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)

from rich.console import Console
from web3 import Web3

from config.constants.emissions import (
    REWARD_ERROR_TOLERANCE,
    ZERO_CYCLE,
    NATIVE_TOKEN_REWARDS,
    SCHEDULE_REWARDS_BLACKLIST,
    TREE_REWARDS_BLACKLIST
)
from helpers.enums import Network
from rewards.classes.RewardsList import RewardsList
from rewards.classes.Snapshot import Snapshot
from rewards.utils.token_utils import token_amount_base_10

console = Console()


def get_cumulative_claimable_for_token(claim, token: str) -> int:
    tokens = claim["tokens"]
    amounts = claim["cumulativeAmounts"]

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


def distribute_rewards_from_total_snapshot(
        amount: Union[int, Decimal], snapshot: Snapshot, token: str,
        block: int, custom_rewards: Optional[Dict[str, Callable]] = {},
) -> RewardsList:
    rewards = RewardsList()
    custom_rewards_list = []
    # Blacklist digg/badger rewards
    if token in NATIVE_TOKEN_REWARDS[snapshot.chain]:
        for addr in SCHEDULE_REWARDS_BLACKLIST.keys():
            snapshot.zero_balance(addr)
    # Blacklist all token rewards for tree rewards blacklist
    for addr in TREE_REWARDS_BLACKLIST.keys():
        snapshot.zero_balance(addr)
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


def merkle_tree_to_rewards_list(tree) -> RewardsList:
    return process_cumulative_rewards(tree, RewardsList(int(tree["cycle"])))


def get_actual_expected_totals(
        sett_totals: Dict[str, Dict[str, Decimal]]
) -> Tuple[Dict[str, Decimal], Dict[str, Decimal]]:
    """Takes dictionary of tokens to be distributed to each sett and returns two dictionaries
    containing the total amount of each token that has been calculated
    to be distributed (actual_totals) and is expected to be distributed
    based on the rewards schedules (expected_totals).

    Args:
        sett_totals (Dict[str, Dict[str, Decimal]])
            {
                "sett1": {
                    "actual": {
                        "token1": actual_amount,
                        "token2": actual_amount,
                        ...
                    },
                    "expected": {
                        "token1": expected_amount,
                        "token2": expected_amount,
                        ...,
                    },
                ...,
            }

    Returns:
        Tuple[Dict[str, Decimal], Dict[str, Decimal]]
        (
            {
                "token1": act_total_amount_to_be_dist_t1,
                "token2": act_total_amount_to_be_dist_t2,
            },
            {
                "token1": exp_total_amount_to_be_dist_t1,
                "token2": exp_total_amount_to_be_dist_t2,
            }
        )

    """
    actual_totals = defaultdict(Decimal)
    expected_totals = defaultdict(Decimal)

    for _, dists in sett_totals.items():
        for dist_type, rewards in dists.items():
            for token, amount in rewards.items():
                if dist_type == "actual":
                    actual_totals[token] += amount
                elif dist_type == "expected":
                    expected_totals[token] += amount

    return actual_totals, expected_totals


def check_token_totals_in_range(
        chain: Network,
        rewards_per_sett: Dict[str, Dict[str, Dict[str, Decimal]]]
) -> List[Optional[List[str]]]:
    """Check that the total amount of tokens to be distributed falls within the expected range
    based on the rewards schedules.

    Args:
        rewards_per_sett (Dict[str, Dict[str, Dict[str, Decimal]]]): actual and expected reward
            amounts for each token to be distributed to each sett

    Returns:
        List[Optional[List[str]]]: list of tokens with invalid distribution amounts
    """
    actual_totals, expected_totals = get_actual_expected_totals(rewards_per_sett)
    invalid_totals = []

    for token in expected_totals.keys():
        min_expected = expected_totals[token] * Decimal(1 - REWARD_ERROR_TOLERANCE)
        max_expected = expected_totals[token] * Decimal(1 + REWARD_ERROR_TOLERANCE)
        actual = actual_totals[token]
        if actual < min_expected or actual > max_expected:
            min_expected = token_amount_base_10(chain, token, min_expected)
            max_expected = token_amount_base_10(chain, token, max_expected)
            actual = token_amount_base_10(chain, token, actual)
            invalid_totals.append([token, min_expected, max_expected, actual])

    return invalid_totals
