from classes.UserBalance import UserBalance, UserBalances

from helpers.constants import (
    NO_GEYSERS,
    REWARDS_BLACKLIST,
)
from helpers.graphql import fetch_sett_balances, fetch_geyser_events

from collections import Counter
from functools import lru_cache
from rich.console import Console


console = Console()


def combine_balances(balances):
    allBalances = UserBalances()
    for userBalances in balances:
        allBalances = allBalances + userBalances
    return allBalances


def filter_dust(balances):
    return UserBalances(list(filter(lambda user: user.balance > 1, balances)))


def calc_union_addresses(diggSetts, badgerSetts, nonNativeSetts):
    return set.union(
        *[
            {user.address for user in diggSetts},
            {user.address for user in badgerSetts},
            {user.address for user in nonNativeSetts},
        ]
    )


def calc_stake_ratio(address, diggSetts, badgerSetts, nonNativeSetts):
    diggBalance = getattr(diggSetts[address], "balance", 0)
    badgerBalance = getattr(badgerSetts[address], "balance", 0)
    nonNativeBalance = getattr(nonNativeSetts[address], "balance", 0)
    if nonNativeBalance == 0:
        stakeRatio = 0
    else:
        stakeRatio = (diggBalance + badgerBalance) / nonNativeBalance
    return stakeRatio


def calc_balances_from_geyser_events(geyserEvents):
    balances = {}
    events = [*geyserEvents["stakes"], *geyserEvents["unstakes"]]
    events = sorted(events, key=lambda e: e["timestamp"])
    currentTime = 0
    for event in events:
        timestamp = int(event["timestamp"])
        assert timestamp >= currentTime
        balances[event["user"]] = int(event["total"])

    console.log("Sum of geyser balances: {}".format(sum(balances.values()) / 10 ** 18))
    console.log("Fetched {} geyser balances".format(len(balances)))
    return balances


@lru_cache(maxsize=None)
def calculate_sett_balances(name, currentBlock, underlyingToken, geyserAddr=""):
    console.log("Fetching {} sett balances".format(name))
    settType = ["", ""]
    if "uni" in name or "sushi" in name:
        settType[0] = "halfLP"
    if "crv" in name.lower() or name == "experimental.sushiIBbtcWbtc":
        settType[0] = "fullLP"
    if "badger" in name.lower() or "digg" in name.lower() or "eth" in name.lower():
        settType[1] = "nonNative"
    else:
        settType[1] = "native"

    settBalances = fetch_sett_balances(name, underlyingToken.lower(), currentBlock)
    geyserBalances = {}
    creamBalances = {}

    if name not in NO_GEYSERS:

        geyserEvents = fetch_geyser_events(geyserAddr, currentBlock)
        geyserBalances = calc_balances_from_geyser_events(geyserEvents)
        settBalances[geyserAddr] = 0

    balances = {}
    for b in [settBalances, geyserBalances, creamBalances]:
        balances = dict(Counter(balances) + Counter(b))

    # Get rid of blacklisted and negative balances
    for addr, balance in list(balances.items()):
        if addr.lower() in REWARDS_BLACKLIST:
            console.log(
                "Removing {} from balances".format(REWARDS_BLACKLIST[addr.lower()])
            )
            del balances[addr]
        if balance < 0:
            del balances[addr]

    # Testing for peak address
    # balances["0x41671BA1abcbA387b9b2B752c205e22e916BE6e3".lower()] = 10000
    userBalances = [
        UserBalance(addr, bal, underlyingToken, settType)
        for addr, bal in balances.items()
    ]
    console.log("\n")
    return UserBalances(userBalances)
