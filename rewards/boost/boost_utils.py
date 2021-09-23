from helpers.constants import BOOST_CHAINS, DISABLED_VAULTS
from helpers.discord import send_message_to_discord
from rewards.snapshot.token_snapshot import token_snapshot_usd
from rewards.explorer import convert_from_eth
from rich.console import Console
from config.env_config import env_config
from rewards.classes.UserBalance import UserBalances
from typing import Dict, List, Tuple
from collections import Counter
from rewards.snapshot.chain_snapshot import chain_snapshot
from badger_api.prices import (
    fetch_token_prices,
)

console = Console()
prices = fetch_token_prices()


def calc_union_addresses(
    native_setts: Dict[str, int], non_native_setts: Dict[str, int]
) -> List[str]:
    """
    Combine addresses from native setts and non native setts
    :param native_setts: native setts
    :param non_native_setts: non native setts
    """
    native_addresses = list(native_setts.keys())
    non_native_addresses = list(non_native_setts.keys())
    return list(set(native_addresses + non_native_addresses))


def filter_dust(balances: Dict[str, int], dust_amount: int) -> Dict[str, float]:
    """
    Filter out dust values from user balances
    :param balances: balances to filter
    :param dust_amount: dollar amount to filter by
    """
    return {addr: value for addr, value in balances.items() if value > dust_amount}


def convert_balances_to_usd(
    balances: UserBalances, sett: str
) -> Tuple[Dict[str, float], str]:
    """
    Convert sett balance to usd and multiply by correct ratio
    :param balances: balances to convert to usd
    """
    sett = env_config.get_web3().toChecksumAddress(sett)
    if sett not in prices:
        price = 0
        send_message_to_discord(
            "**BADGER BOOST ERROR**",
            f"Cannot find pricing for f{sett}",
            [],
            "Boost Bot",
        )
    else:
        price = prices[sett]

    price_ratio = balances.sett_ratio
    usd_balances = {}
    for user in balances:
        usd_balances[user.address] = price_ratio * price * user.balance

    return usd_balances, balances.sett_type


def calc_boost_balances(block: int) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Calculate boost data required for boost calculation
    :param block: block to collect the boost data from
    """

    blocks_by_chain = convert_from_eth(block)
    native = Counter()
    non_native = Counter()
    for chain in BOOST_CHAINS:
        chain_block = blocks_by_chain[chain]
        console.log(f"Taking chain snapshot on {chain} \n")

        snapshot = chain_snapshot(chain, chain_block)
        console.log(f"Taking token snapshot on {chain}")

        tokens = token_snapshot_usd(chain, chain_block)
        native = native + Counter(tokens)
        for sett, balances in snapshot.items():
            if sett in DISABLED_VAULTS:
                continue
            balances, sett_type = convert_balances_to_usd(balances, sett)
            if sett_type == "native":
                native = native + Counter(balances)
            elif sett_type == "nonNative":
                non_native = non_native + Counter(balances)

    native = filter_dust(dict(native), 1)
    non_native = filter_dust(dict(non_native), 1)
    return native, non_native
