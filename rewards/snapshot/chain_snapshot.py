from config.env_config import env_config
from helpers.constants import REWARDS_BLACKLIST, SETT_INFO
from helpers.web3_utils import make_contract
from rewards.classes.UserBalance import UserBalances, UserBalance
from subgraph.client import fetch_chain_balances, fetch_sett_balances
from functools import lru_cache
from rich.console import Console
from typing import Dict, Tuple

console = Console()


@lru_cache(maxsize=128)
def chain_snapshot(chain: str, block: int) -> Dict[str, UserBalances]:
    """
    Take a snapshot of a chains sett balances at a certain block

    :param badger: badger system
    :param chain: chain to query
    :param block: block at which to query

    """
    chainBalances = fetch_chain_balances(chain, block)
    balancesBySett = {}

    for settAddr, balances in list(chainBalances.items()):
        settBalances = parse_sett_balances(settAddr, balances)
        token = make_contract(settAddr, abiName="ERC20", chain=chain)
        console.log(
            "Fetched {} balances for sett {}".format(
                len(balances), token.functions.name().call()
            )
        )
        balancesBySett[settAddr] = settBalances

    return balancesBySett


@lru_cache(maxsize=128)
def sett_snapshot(chain: str, block: int, sett: str) -> UserBalances:
    """
    Take a snapshot of a sett on a chain at a certain block
    :param chain:
    :param block:
    :param sett:
    """
    token = make_contract(sett, abiName="ERC20", chain=chain)
    console.log(
        "Taking snapshot on {} of {} at {}".format(
            chain, sett, token.functions.name().call()
        )
    )
    sett_balances = fetch_sett_balances(chain, block - 50, sett)
    return parse_sett_balances(sett, sett_balances)


def parse_sett_balances(settAddress: str, balances: Dict[str, int]) -> UserBalances:
    """
    Blacklist balances and add metadata for boost
    :param balances: balances of users:
    :param chain: chain where balances come from
    """
    for addr, balance in list(balances.items()):
        if addr.lower() in REWARDS_BLACKLIST:
            console.log(
                "Removing {} from balances".format(REWARDS_BLACKLIST[addr.lower()])
            )
            del balances[addr]

    settType, settRatio = get_sett_info(settAddress)
    console.log(
        "Sett {} has type {} and Ratio {} \n".format(settAddress, settType, settRatio)
    )
    userBalances = [
        UserBalance(addr, bal, settAddress) for addr, bal in balances.items()
    ]
    return UserBalances(userBalances, settType, settRatio)


def get_sett_info(settAddress) -> Tuple[str,float]:
    info = SETT_INFO.get(
        env_config.get_web3().toChecksumAddress(settAddress),
        {"type": "nonNative", "ratio": 1},
    )
    return info["type"], info["ratio"]
