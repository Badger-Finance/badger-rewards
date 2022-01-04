from typing import Any, Dict, List, Tuple

from rich.console import Console
from tabulate import tabulate

from helpers.constants import BOOST_BLOCK_DELAY, STAKE_RATIO_RANGES
from helpers.discord import get_discord_url, send_code_block_to_discord
from helpers.enums import BotType
from rewards.boost.boost_utils import calc_boost_balances, calc_union_addresses
from subgraph.queries.nfts import fetch_nfts

console = Console()


def calc_stake_ratio(
    address: str, native_setts: Dict[str, float], non_native_setts: Dict[str, float]
) -> int:
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
        stake_ratio = native_balance / non_native_balance
    return stake_ratio


def get_badger_boost_data(stake_ratios: Dict) -> Tuple[Dict, Dict]:
    badger_boost_data = {}
    stake_data_ranges = {}
    for addr, stake_ratio in stake_ratios.items():
        user_boost = 1
        user_stake_range = 0
        for stake_range, multiplier in STAKE_RATIO_RANGES:
            if stake_ratio > stake_range:
                user_boost = multiplier
                user_stake_range = stake_range

        stake_data_ranges[user_stake_range] = stake_data_ranges.get(user_stake_range, 0) + 1
        badger_boost_data[addr] = user_boost if stake_ratio != 0 else 1
    return badger_boost_data, stake_data_ranges


def init_boost_data(addresses: List[str]) -> Dict[str, Any]:
    boost_info = {}
    for addr in addresses:
        boost_info[addr] = {
            "nativeBalance": 0,
            "nonNativeBalance": 0,
            "stakeRatio": 0,
            "nftBalance": 0,
            "nfts": [],
        }

    return boost_info


def allocate_nft_balances_to_users(boost_info: Dict, nft_balances: Dict) -> None:
    for user, nft_balance in nft_balances.items():
        boost_info[user]["nftBalance"] = nft_balance


def allocate_nft_to_users(boost_info: Dict, addresses: List[str], nfts: Dict):
    for user, nft_balances in nfts.items():
        if user in addresses:
            boost_info[user]["nfts"] = nft_balances


def assign_stake_ratio_to_users(boost_info: Dict, stake_ratios: Dict) -> None:
    for user, ratio in stake_ratios.items():
        boost_info[user]["stakeRatio"] = ratio


def assign_native_balances_to_users(boost_info: Dict, native_setts: Dict):
    for user, native_usd in native_setts.items():
        boost_info[user]["nativeBalance"] = native_usd


def assign_non_native_balances_to_users(boost_info: Dict, non_native_setts: Dict):
    for user, non_native_usd in non_native_setts.items():
        boost_info[user]["nonNativeBalance"] = non_native_usd


def badger_boost(current_block: int, chain: str) -> Dict[str, Any]:
    """
    Calculate badger boost multipliers based on stake ratios
    :param current_block: block to calculate boost at
    :param chain: target chain
    """
    discord_url = get_discord_url(chain, BotType.Boost)
    console.log(f"Calculating boost at block {current_block} ...")
    native_setts, non_native_setts, nft_balances = calc_boost_balances(
        current_block - BOOST_BLOCK_DELAY, chain
    )

    all_addresses = calc_union_addresses(native_setts, non_native_setts)
    console.log(f"{len(all_addresses)} addresses fetched")
    boost_data = {}

    stake_ratios_list = [
        calc_stake_ratio(addr, native_setts, non_native_setts) for addr in all_addresses
    ]
    stake_ratios = dict(zip(all_addresses, stake_ratios_list))
    badger_boost_data, stake_data = get_badger_boost_data(stake_ratios)
    nfts = fetch_nfts(chain, current_block)

    boost_info = init_boost_data(all_addresses)
    allocate_nft_balances_to_users(boost_info, nft_balances)
    allocate_nft_to_users(boost_info, all_addresses, nfts)
    assign_stake_ratio_to_users(boost_info, stake_ratios)
    assign_native_balances_to_users(boost_info, native_setts)
    assign_non_native_balances_to_users(boost_info, non_native_setts)

    for addr, boost in badger_boost_data.items():
        boost_metadata = boost_info.get(addr, {})
        boost_data[addr] = {
            "boost": boost,
            "nativeBalance": boost_metadata.get("nativeBalance", 0),
            "nonNativeBalance": boost_metadata.get("nonNativeBalance", 0),
            "nftBalance": boost_metadata.get("nftBalance", 0),
            "stakeRatio": boost_metadata.get("stakeRatio", 0),
            "multipliers": {},
            "nfts": boost_metadata.get("nfts", [])
        }

    stake_data = {k: stake_data[k] for k in sorted(stake_data, reverse=True)}

    stake_data_table = tabulate(
        [[rng, amount] for rng, amount in stake_data.items()],
        headers=["range", "amount of users"],
    )
    print(stake_data_table)
    send_code_block_to_discord(stake_data_table, username="Boost Bot", url=discord_url)

    return boost_data
