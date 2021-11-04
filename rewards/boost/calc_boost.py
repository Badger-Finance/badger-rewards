from rich.console import Console
from helpers.constants import (
    BOOST_BLOCK_DELAY,
    STAKE_RATIO_RANGES,
)
from typing import Dict
from tabulate import tabulate
from helpers.discord import send_code_block_to_discord
from rewards.boost.boost_utils import (
    calc_union_addresses,
    calc_boost_balances,
)
from web3 import Web3

console = Console()


def calc_stake_ratio(
    address: str, native_setts: Dict[str, int], non_native_setts: Dict[str, int]
):
    """
    Calculate the stake ratio for an address
    :param address: address to find stake ratio for
    :param native_setts: native balances
    :param non_native_setts: non native balances
    """
    native_balance = native_setts.get(address, 0)
    non_native_balance = non_native_setts.get(address, 0)
    if non_native_balance == 0 or native_balance == 0:
        stake_ratio = 0
    else:
        stake_ratio = (native_balance) / non_native_balance
    return stake_ratio


def badger_boost(current_block: int, chain: str):
    """
    Calculate badger boost multipliers based on stake ratios
    :param current_block: block to calculate boost at
    """
    console.log(f"Calculating boost at block {current_block} ...")
    native_setts, non_native_setts = calc_boost_balances(
        current_block - BOOST_BLOCK_DELAY, chain
    )

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
        boost_info[addr] = {
            "nativeBalance": 0,
            "nonNativeBalance": 0,
            "stakeRatio": 0,
        }

    for user, native_usd in native_setts.items():
        boost_info[user]["nativeBalance"] = native_usd

    for user, non_native_usd in non_native_setts.items():
        boost_info[user]["nonNativeBalance"] = non_native_usd

    for user, ratio in stake_ratios.items():
        boost_info[user]["stakeRatio"] = ratio

    stake_data = {}
    console.log(STAKE_RATIO_RANGES)
    for addr, stake_ratio in stake_ratios.items():
        if stake_ratio == 0:
            badger_boost[addr] = 1
        else:
            user_boost = 1
            user_stake_range = 0
            for stake_range, multiplier in STAKE_RATIO_RANGES:
                if stake_ratio > stake_range:
                    user_boost = multiplier
                    user_stake_range = stake_range

            stake_data[user_stake_range] = stake_data.get(user_stake_range, 0) + 1
            badger_boost[addr] = user_boost

    for addr, boost in badger_boost.items():
        boost_metadata = boost_info.get(addr, {})
        boost_data[Web3.toChecksumAddress(addr)] = {
            "boost": boost,
            "nativeBalance": boost_metadata.get("nativeBalance", 0),
            "nonNativeBalance": boost_metadata.get("nonNativeBalance", 0),
            "stakeRatio": boost_metadata.get("stakeRatio", 0),
            "multipliers": {},
        }

    stake_data = {k: stake_data[k] for k in sorted(stake_data, reverse=True)}

    stake_data_table = tabulate(
        [[rng, amount] for rng, amount in stake_data.items()],
        headers=["range", "amount of users"],
    )
    print(stake_data_table)
    send_code_block_to_discord(stake_data_table, username="Boost Bot")

    return boost_data
