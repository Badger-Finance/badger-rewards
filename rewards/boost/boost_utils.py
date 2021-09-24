from helpers.constants import BOOST_CHAINS
from helpers.discord import send_message_to_discord
from rewards.explorer import convert_from_eth
from rich.console import Console
from config.env_config import env_config
from typing import Dict, List, Tuple
from collections import Counter
from rewards.snapshot.chain_snapshot import chain_snapshot_usd
from rewards.snapshot.token_snapshot import token_snapshot_usd
from rewards.snapshot.claims_snapshot import claims_snapshot_usd
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


def calc_boost_balances(block: int) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Calculate boost data required for boost calculation
    :param block: block to collect the boost data from
    """

    blocks_by_chain = convert_from_eth(block)
    native = Counter()
    non_native = Counter()

    native_claimable, non_native_claimable = claims_snapshot_usd()
    for chain in BOOST_CHAINS:
        chain_block = blocks_by_chain[chain]

        console.log(f"Taking chain snapshot on {chain} \n")
        if chain != "polygon":
            native_setts, non_native_setts = chain_snapshot_usd(chain, chain_block)
            non_native = non_native + Counter(non_native_setts)
            native = native + Counter(native_setts)

        console.log(f"Taking token snapshot on {chain}")
        badger_tokens, digg_tokens = token_snapshot_usd(chain, chain_block)
        native = native + Counter(badger_tokens) + Counter(digg_tokens)

    native = native + Counter(native_claimable)
    non_native = non_native + Counter(non_native_claimable)

    native = filter_dust(dict(native), 1)
    non_native = filter_dust(dict(non_native), 1)
    return native, non_native
