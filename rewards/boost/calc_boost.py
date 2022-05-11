from decimal import Decimal
import math
from typing import Any, Dict, List, Tuple

from rich.console import Console
from tabulate import tabulate

from config.constants.emissions import (
    BOOST_BLOCK_DELAY,
    BVECVX_BOOST_WEIGHT,
    DIGG_BOOST_WEIGHT,
    STAKE_RATIO_RANGES,
)
from helpers.discord import get_discord_url, send_code_block_to_discord
from helpers.enums import BotType
from rewards.boost.boost_utils import calc_boost_balances, calc_union_addresses
from rewards.classes.Boost import BoostBalances
from rewards.feature_flags import flags
from rewards.feature_flags.feature_flags import BOOST_STEP
from subgraph.queries.nfts import fetch_nfts

console = Console()


def calc_bvecvx_native_balance(native_balance: Decimal, bvecvx_balance: Decimal) -> Decimal:
    """
    Calculate the amoutn of bvecvx to add to a user's native balance
    :param native_balance: user's current native balance
    :param bvecvx_balance: user's total bvecvx balance
    """
    if bvecvx_balance > 0 and native_balance > 0:
        return min(
            Decimal(BVECVX_BOOST_WEIGHT) * bvecvx_balance,
            Decimal(BVECVX_BOOST_WEIGHT) * native_balance
        )
    return Decimal(0)


def calc_digg_native_balance(native_balance: Decimal, digg_balance: Decimal) -> Decimal:
    if digg_balance > 0 and native_balance > 0:
        return min(
            Decimal(DIGG_BOOST_WEIGHT) * digg_balance,
            Decimal(DIGG_BOOST_WEIGHT) * native_balance
        )
    return Decimal(0)


def calc_stake_ratio(address: str, boost_bals: BoostBalances) -> Decimal:
    """
    Calculate the stake ratio for an address
    :param address: address to find stake ratio for
    :param boost_bals: balances data object
    """
    native_balance = Decimal(boost_bals.native.get(address, 0))
    non_native_balance = Decimal(boost_bals.non_native.get(address, 0))
    bvecvx_balance = Decimal(boost_bals.bvecvx.get(address, 0))
    digg_balance = Decimal(boost_bals.digg.get(address, 0))
    native_balance += calc_bvecvx_native_balance(native_balance, bvecvx_balance)
    native_balance += calc_digg_native_balance(native_balance, digg_balance)
    if non_native_balance == 0 or native_balance == 0:
        stake_ratio = 0
    else:
        stake_ratio = native_balance / non_native_balance
    return stake_ratio


def get_badger_boost_data(stake_ratios: Dict) -> Tuple[Dict, Dict]:
    badger_boost_data = {}
    stake_data_ranges = {}
    for addr, stake_ratio in stake_ratios.items():
        user_stake_range = 0
        if flags.flag_enabled(BOOST_STEP):
            if stake_ratio == 0:
                user_boost = 1
            elif stake_ratio <= 1:
                user_boost = min(math.floor(stake_ratio * 2000), 2000)
            elif 1.0 < stake_ratio <= 1.5:
                user_boost = 2000 + \
                    math.floor((stake_ratio - Decimal(1)) * 1000)
            elif 1.5 < stake_ratio <= 2:
                user_boost = 2500 + \
                    math.floor((stake_ratio - Decimal(1.5)) * 500)
            elif stake_ratio > 2:
                user_boost = min(
                    2750 + math.floor((stake_ratio - Decimal(2)) * 250), 3000)
        else:
            user_boost = 1
        for stake_range, multiplier in STAKE_RATIO_RANGES:
            if stake_ratio >= stake_range:
                if not flags.flag_enabled(BOOST_STEP):
                    user_boost = multiplier
                user_stake_range = stake_range
        stake_data_ranges[user_stake_range] = stake_data_ranges.get(
            user_stake_range, 0) + 1
        badger_boost_data[addr] = user_boost
    return badger_boost_data, stake_data_ranges


def init_boost_data(addresses: List[str]) -> Dict[str, Any]:
    boost_info = {}
    for addr in addresses:
        boost_info[addr] = {
            "nativeBalance": 0,
            "nonNativeBalance": 0,
            "stakeRatio": 0,
            "bveCvxBalance": 0,
            "diggBalance": 0,
            "nftBalance": 0,
            "nfts": [],
        }

    return boost_info


def allocate_nft_balances_to_users(boost_info: Dict, nft_balances: Dict) -> None:
    for user, nft_balance in nft_balances.items():
        boost_info[user]["nftBalance"] = nft_balance


def allocate_bvecvx_to_users(boost_info: Dict, bvecvx_balances: Dict):
    for user, bvecvx_balance in bvecvx_balances.items():
        native_balance = boost_info.get(
            user, {}).get("nativeBalance", Decimal(0))
        calculated_bvecvx_balance = calc_bvecvx_native_balance(
            native_balance, bvecvx_balance)
        if user in boost_info:
            boost_info[user]["bveCvxBalance"] = calculated_bvecvx_balance
            boost_info[user]["nativeBalance"] = native_balance + \
                calculated_bvecvx_balance


def allocate_digg_to_users(boost_info: Dict, digg_balances: Dict):
    for user, digg_balance in digg_balances.items():
        native_balance = boost_info.get(user, {}).get("nativeBalance", Decimal(0))
        calculated_digg_balance = calc_digg_native_balance(native_balance, digg_balance)
        if user in boost_info:
            boost_info[user]["diggBalance"] = calculated_digg_balance
            boost_info[user]["nativeBalance"] = native_balance + calculated_digg_balance


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
    boost_bals = calc_boost_balances(current_block - BOOST_BLOCK_DELAY, chain)

    all_addresses = calc_union_addresses(
        boost_bals.native, boost_bals.non_native)
    console.log(f"{len(all_addresses)} addresses fetched")
    boost_data = {}

    stake_ratios_list = [calc_stake_ratio(
        addr, boost_bals) for addr in all_addresses]
    stake_ratios = dict(zip(all_addresses, stake_ratios_list))
    badger_boost_data, stake_data = get_badger_boost_data(stake_ratios)
    nfts = fetch_nfts(chain, current_block)

    boost_info = init_boost_data(all_addresses)
    allocate_nft_balances_to_users(boost_info, boost_bals.nfts)
    allocate_nft_to_users(boost_info, all_addresses, nfts)
    assign_stake_ratio_to_users(boost_info, stake_ratios)
    assign_native_balances_to_users(boost_info, boost_bals.native)
    assign_non_native_balances_to_users(boost_info, boost_bals.non_native)
    allocate_bvecvx_to_users(boost_info, boost_bals.bvecvx)
    allocate_digg_to_users(boost_info, boost_bals.digg)

    for addr, boost in badger_boost_data.items():
        boost_metadata = boost_info.get(addr, {})
        boost_data[addr] = {
            "boost": boost,
            "nativeBalance": boost_metadata.get("nativeBalance", 0),
            "nonNativeBalance": boost_metadata.get("nonNativeBalance", 0),
            "bveCvxBalance": boost_metadata.get("bveCvxBalance", 0),
            "diggBalance": boost_metadata.get("diggBalance", 0),
            "nftBalance": boost_metadata.get("nftBalance", 0),
            "stakeRatio": boost_metadata.get("stakeRatio", 0),
            "multipliers": {},
            "nfts": boost_metadata.get("nfts", []),
        }

    stake_data = {k: stake_data[k] for k in sorted(stake_data, reverse=True)}

    stake_data_table = tabulate(
        [[rng, amount] for rng, amount in stake_data.items()],
        headers=["range", "amount of users"],
    )
    print(stake_data_table)
    send_code_block_to_discord(
        stake_data_table, username="Boost Bot", url=discord_url)

    return boost_data
