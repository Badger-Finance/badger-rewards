from rewards.classes.Snapshot import Snapshot
from config.env_config import env_config
from helpers.constants import (
    REWARDS_BLACKLIST,
    SETT_INFO,
    DISABLED_VAULTS,
    EMISSIONS_BLACKLIST,
    PRO_RATA_VAULTS,
)
from helpers.web3_utils import make_contract
from subgraph.queries.setts import fetch_chain_balances, fetch_sett_balances
from rich.console import Console
from typing import Dict, Tuple
from collections import Counter
from web3 import Web3

console = Console()


def chain_snapshot(chain: str, block: int) -> Dict[str, Snapshot]:
    """
    Take a snapshot of a chains sett balances at a certain block

    :param badger: badger system
    :param chain: chain to query
    :param block: block at which to query

    """
    chain_balances = fetch_chain_balances(chain, block)
    balances_by_sett = {}

    for sett_addr, balances in list(chain_balances.items()):
        sett_balances = parse_sett_balances(sett_addr, balances)
        token = make_contract(sett_addr, abi_name="ERC20", chain=chain)
        console.log(f"Fetched {len(balances)} balances for sett {token.name().call()}")
        balances_by_sett[sett_addr] = sett_balances

    return balances_by_sett


def sett_snapshot(chain: str, block: int, sett: str, blacklist: bool) -> Snapshot:
    """
    Take a snapshot of a sett on a chain at a certain block
    :param chain:
    :param block:
    :param sett:
    """
    token = make_contract(sett, abi_name="ERC20", chain=chain)
    console.log(
        f"Taking snapshot on {chain} of {token.name().call()} ({sett}) at {block}\n"
    )
    sett_balances = fetch_sett_balances(chain, block - 50, sett)
    return parse_sett_balances(sett, sett_balances, blacklist)


def parse_sett_balances(
    sett_address: str, balances: Dict[str, int], blacklist: bool = True
) -> Snapshot:
    """
    Blacklist balances and add metadata for boost
    :param balances: balances of users:
    :param chain: chain where balances come from
    """
    if blacklist:
        addresses_to_blacklist = {**REWARDS_BLACKLIST, **EMISSIONS_BLACKLIST}
    else:
        addresses_to_blacklist = REWARDS_BLACKLIST

    for addr, balance in list(balances.items()):
        addr = Web3.toChecksumAddress(addr)
        if addr in addresses_to_blacklist:
            console.log(f"Removing {addresses_to_blacklist[addr]} from balances")
            del balances[addr.lower()]

    sett_type, sett_ratio = get_sett_info(sett_address)
    console.log(f"Sett {sett_address} has type {sett_type} and ratio {sett_ratio} \n")

    return Snapshot(sett_address, balances, sett_ratio, sett_type)


def get_sett_info(sett_address: str) -> Tuple[str, float]:
    info = SETT_INFO.get(
        env_config.get_web3().toChecksumAddress(sett_address),
        {"type": "nonNative", "ratio": 1},
    )
    console.log(sett_address, info)
    return info["type"], info["ratio"]


def chain_snapshot_usd(chain: str, block: int) -> Tuple[Counter, Counter]:
    """Take a snapshot of a chains native/non native balances in usd"""
    total_snapshot = chain_snapshot(chain, block)
    native = Counter()
    non_native = Counter()
    for sett, snapshot in total_snapshot.items():
        sett = env_config.get_web3().toChecksumAddress(sett)
        if sett in [*DISABLED_VAULTS, *PRO_RATA_VAULTS]:
            console.log(f"{sett} is disabled")
            continue
        usd_snapshot = snapshot.convert_to_usd()
        balances = Counter(usd_snapshot.balances)
        if usd_snapshot.type == "native":
            native = native + balances
        elif usd_snapshot.type == "nonNative":
            non_native = non_native + balances

    return native, non_native
