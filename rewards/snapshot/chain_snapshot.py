from config.env_config import env_config
from helpers.constants import REWARDS_BLACKLIST, SETT_INFO, DISABLED_VAULTS
from helpers.web3_utils import make_contract
from helpers.discord import send_message_to_discord
from rewards.classes.UserBalance import UserBalances, UserBalance
from subgraph.queries.setts import fetch_chain_balances, fetch_sett_balances
from functools import lru_cache
from rich.console import Console
from typing import Dict, Tuple
from collections import Counter
from badger_api import fetch_token_prices

console = Console()


@lru_cache(maxsize=128)
def chain_snapshot(chain: str, block: int) -> Dict[str, UserBalances]:
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


@lru_cache(maxsize=128)
def sett_snapshot(chain: str, block: int, sett: str) -> UserBalances:
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
    return parse_sett_balances(sett, sett_balances)


def parse_sett_balances(sett_address: str, balances: Dict[str, int]) -> UserBalances:
    """
    Blacklist balances and add metadata for boost
    :param balances: balances of users:
    :param chain: chain where balances come from
    """
    for addr, balance in list(balances.items()):
        if addr.lower() in REWARDS_BLACKLIST:
            console.log(f"Removing {REWARDS_BLACKLIST[addr.lower()]} from balances")
            del balances[addr]

    sett_type, sett_ratio = get_sett_info(sett_address)
    console.log(f"Sett {sett_address} has type {sett_type} and Ratio {sett_ratio} \n")
    user_balances = [
        UserBalance(addr, bal, sett_address) for addr, bal in balances.items()
    ]
    return UserBalances(user_balances, sett_type, sett_ratio)


def get_sett_info(sett_address: str) -> Tuple[str, float]:
    info = SETT_INFO.get(
        env_config.get_web3().toChecksumAddress(sett_address),
        {"type": "nonNative", "ratio": 1},
    )
    return info["type"], info["ratio"]


def claim_snapshot_usd(chain: str, block: int):
    snapshot = claims_snapshot(chain, block)
    native = Counter()
    non_native = Counter()
    for sett, balances in snapshot.items():
        if sett in DISABLED_VAULTS:
            continue
        balances, sett_type = convert_balances_to_usd(balances, sett)
        if sett_type == "native":
            native = native + Counter(balances)
        elif sett_type == "nonNative":
            non_native = non_native + Counter(balances)

    return native, non_native


def convert_balances_to_usd(
    balances: UserBalances, sett: str
) -> Tuple[Dict[str, float], str]:
    """
    Convert sett balance to usd and multiply by correct ratio
    :param balances: balances to convert to usd
    """

    price = fetch_token_prices()
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
