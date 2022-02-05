from collections import Counter, namedtuple
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Tuple
from rich.console import Console
from helpers.enums import Network
import config.constants.addresses as addresses
from rewards.snapshot.chain_snapshot import chain_snapshot_usd, sett_snapshot
from rewards.snapshot.claims_snapshot import claims_snapshot, claims_snapshot_usd
from rewards.snapshot.nft_snapshot import nft_snapshot_usd
from rewards.snapshot.token_snapshot import token_snapshot_usd
from rewards.classes.Boost import BoostBalances, BoostData

console = Console()


dataclass


def calc_union_addresses(
    native_setts: Dict[str, float], non_native_setts: Dict[str, float]
) -> List[str]:
    """
    Combine addresses from native setts and non native setts
    :param native_setts: native setts
    :param non_native_setts: non native setts
    """
    native_addresses = list(native_setts.keys())
    non_native_addresses = list(non_native_setts.keys())
    return list(set(native_addresses + non_native_addresses))


def filter_dust(balances: Dict[str, float], dust_amount: int) -> Dict[str, float]:
    """
    Filter out dust values from user balances
    :param balances: balances to filter
    :param dust_amount: dollar amount to filter by
    """
    return {addr: value for addr, value in balances.items() if value > dust_amount}


def calc_boost_balances(block: int, chain: str) -> BoostBalances:
    """
    Calculate boost data required for boost calculation
    :param block: block to collect the boost data from
    :param chain: target chain
    """

    native = Counter()
    non_native = Counter()

    bvecvx_bals = sett_snapshot(chain, block, addresses.BVECVX, blacklist=True)
    console.log(f"\n === Taking claims snapshot on {chain} === \n")
    native_claimable, non_native_claimable = claims_snapshot_usd(chain, block)
    bvecvx_claimable = claims_snapshot(chain, block)[addresses.BVECVX]

    bvecvx_usd = (bvecvx_bals + bvecvx_claimable).convert_to_usd().balances
    native += Counter(native_claimable)
    non_native += Counter(non_native_claimable)
    console.log(f"\n === Taking nft snapshot on {chain} === \n")
    nft_balances = nft_snapshot_usd(chain, block)

    console.log(f"\n === Taking token snapshot on {chain} === \n")
    badger_tokens, digg_tokens = token_snapshot_usd(chain, block)

    native += Counter(badger_tokens) + Counter(digg_tokens) + Counter(nft_balances)

    console.log(f"\n === Taking chain snapshot on {chain} === \n")
    native_setts, non_native_setts = chain_snapshot_usd(chain, block)
    non_native += Counter(non_native_setts)
    native += Counter(native_setts)

    native = filter_dust(dict(native), 1)
    non_native = filter_dust(dict(non_native), 1)
    return BoostBalances(native, non_native, bvecvx_usd, nft_balances)
