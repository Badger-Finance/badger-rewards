from rich.console import Console
from helpers.constants import (
    STAKE_RATIO_RANGES,
)
from typing import Dict
from tabulate import tabulate

from rewards.boost.boost_utils import (
    calc_union_addresses,
    calc_boost_balances,
)

console = Console()


def calc_stake_ratio(
    address: str, native_setts: Dict[str, int], non_native_setts: Dict[str, int]
):
    """
    Calculate the stake ratio for an address
    :param address: address to find stake ratio for
    :param nativeSetts: native balances
    :param nonNativeSetts: non native balances
    """
    native_balance = native_setts.get(address.lower(), 0)
    non_native_balance = non_native_setts.get(address.lower(), 0)
    if non_native_balance == 0 or native_balance == 0:
        stake_ratio = 0
    else:
        stake_ratio = (native_balance) / non_native_balance
    return stake_ratio


def badger_boost(current_block: int):
    """
    Calculate badger boost multipliers based on stake ratios
    :param badger: badger system
    :param currentBlock: block to calculate boost at
    """
    console.log(f"Calculating boost at block {current_block} ...")
    native_setts, non_native_setts = calc_boost_balances(current_block - 10)

    all_addresses = calc_union_addresses(native_setts, non_native_setts)
    console.log(f"{len(all_addresses)} addresses fetched")
    badger_boost = {}
    boost_info = {}
    boost_data = {}

    stake_ratios_list = [
        calc_stake_ratio(addr, native_setts, non_native_setts) for addr in all_addresses
    ]

    stake_ratios = dict(zip(all_addresses, stake_ratios_list))

    for addr in all_addresses:
        boost_info[addr] = {"nativeBalance": 0, "nonNativeBalance": 0, "stakeRatio": 0}

    for user, nativeUsd in native_setts.items():
        boost_info[user.lower()]["nativeBalance"] = nativeUsd

    for user, nonNativeUsd in non_native_setts.items():
        boost_info[user.lower()]["nonNativeBalance"] = nonNativeUsd

    for addr, ratio in stake_ratios.items():
        boost_info[addr.lower()]["stakeRatio"] = ratio

    stake_data = {}
    console.log(STAKE_RATIO_RANGES)
    for addr, stake_ratio in stake_ratios.items():
        if stake_ratio == 0:
            badger_boost[addr] = 1
        else:
            userBoost = 1
            userStakeRange = 0
            for stakeRange, multiplier in STAKE_RATIO_RANGES:
                if stake_ratio > stakeRange:
                    userBoost = multiplier
                    userStakeRange = stakeRange

            stake_data[userStakeRange] = stake_data.get(userStakeRange, 0) + 1
            badger_boost[addr] = userBoost

    for addr, boost in badger_boost.items():
        boost_metadata = boost_info.get(addr, {})
        boost_data[addr] = {
            "boost": boost,
            "nativeBalance": boost_metadata.get("nativeBalance", 0),
            "nonNativeBalance": boost_metadata.get("nonNativeBalance", 0),
            "stakeRatio": boost_metadata.get("stakeRatio", 0),
            "multipliers": {},
        }

    print(
        tabulate(
            [[rng, amount] for rng, amount in stake_data.items()],
            headers=["range", "amount of users"],
        )
    )

    return boost_data
