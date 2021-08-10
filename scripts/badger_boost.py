from classes.RewardsList import RewardsList
from classes.UserBalance import UserBalance, UserBalances

from helpers.api import fetch_token_prices
from helpers.aws import upload_boosts
from helpers.calc_snapshot import calc_snapshot
from helpers.rewards_utils import calculate_sett_balances, calc_stake_ratio, calc_union_addresses, combine_balances, filter_dust
from helpers.constants import (
    DIGG,
    MAX_BOOST,
    SETT_BOOST_RATIOS,
    BADGER,
    STAKE_RATIO_RANGES
)
from helpers.graphql import fetch_wallet_balances
from helpers.time_utils import to_hours, to_utc_date

from collections import OrderedDict
import json
from rich.console import Console
from tabulate import tabulate


console = Console()
prices = fetch_token_prices()


def combine_rewards(rewardsList, cycle, badgerTree):
    combinedRewards = RewardsList(cycle, badgerTree)
    for rewards in rewardsList:
        for user, claims in rewards.claims.items():
            for token, claim in claims.items():
                combinedRewards.increase_user_rewards(user, token, claim)
    return combinedRewards


def get_distributed_for_token_at(token, endTime, schedules, name):
    totalToDistribute = 0
    for index, schedule in enumerate(schedules):
        if endTime < schedule.startTime:
            toDistribute = 0
            console.log("\nSchedule {} for {} completed\n".format(index, name))
        else:
            rangeDuration = endTime - schedule.startTime
            toDistribute = min(
                schedule.initialTokensLocked,
                int(schedule.initialTokensLocked * rangeDuration // schedule.duration),
            )
            if schedule.startTime <= endTime and schedule.endTime >= endTime:
                console.log(
                    "Tokens distributed by schedule {} at {} are {}% of total\n".format(
                        index,
                        to_utc_date(schedule.startTime),
                        (int(toDistribute) / int(schedule.initialTokensLocked) * 100),
                    )
                )

                console.log(
                    "Total duration of schedule elapsed is {} hours out of {} hours, or {}% of total duration.\n".format(
                        to_hours(rangeDuration),
                        to_hours(schedule.duration),
                        rangeDuration / schedule.duration * 100,
                    )
                )
        totalToDistribute += toDistribute
    return totalToDistribute


def calc_boost(percentages):
    boosts = []
    for p in percentages:
        boost = MAX_BOOST - (p * (MAX_BOOST - 1))
        if boost < 1:
            boost = 1
        boosts.append(boost)
    return boosts


def calc_sett_rewards(badger, periodStartBlock, endBlock, cycle, unclaimedRewards):
    """
    Calculate rewards for each sett, and sum them
    """
    rewardsBySett = {}
    noRewards = [
        "native.digg",
        "experimental.digg",
        "native.mstableImBtc",
        "native.mstableFpMbtcHbtc",
    ]
    boosts, boostInfo = badger_boost(badger, endBlock)
    apyBoosts = {}
    multiplierData = {}
    for key, sett in badger.sett_system.vaults.items():
        if key in noRewards:
            continue

        settRewards, apyBoost = calc_snapshot(
            badger, key, periodStartBlock, endBlock, cycle, boosts, unclaimedRewards
        )
        if len(apyBoost) > 0:
            minimum = min(apyBoost.values())
            maximum = max(apyBoost.values())
            multiplierData[sett.address] = {"min": minimum, "max": maximum}
            for addr in apyBoost:
                if addr not in apyBoosts:
                    apyBoosts[addr] = {}
                apyBoosts[addr][sett.address] = apyBoost[addr]

        rewardsBySett[key] = settRewards

    rewards = combine_rewards(list(rewardsBySett.values()), cycle, badger.badgerTree)
    boostsMetadata = {"multiplierData": multiplierData, "userData": {}}

    for addr, multipliers in apyBoosts.items():
        boostsMetadata["userData"][addr] = {
            "boost": boosts.get(addr, 1),
            "multipliers": multipliers,
            "nonNativeBalance": boostInfo.get(addr, {}).get("nonNativeBalance", 0),
            "nativeBalance": boostInfo.get(addr, {}).get("nativeBalance", 0),
            "stakeRatio": boostInfo.get(addr, {}).get("stakeRatio", 0),
        }

    with open("badger-boosts.json", "w") as fp:
        json.dump(boostsMetadata, fp)

    upload_boosts(test=False)

    return rewards

def convert_balances_to_usd(sett, name, userBalances):
    tokenAddress = sett.address
    price = prices[tokenAddress]
    decimals = interface.IERC20(tokenAddress).decimals()
    price_ratio = SETT_BOOST_RATIOS[name]

    for user in userBalances:
        user.balance = (price_ratio * price * user.balance) / (pow(10, decimals))

    return userBalances

def badger_boost(badger, currentBlock):
    console.log("Calculating boost ...")
    allSetts = badger.sett_system.vaults
    diggSetts = UserBalances()
    badgerSetts = UserBalances()
    nonNativeSetts = UserBalances()
    boostInfo = {}
    noBoost = [
        "experimental.digg",
        "native.mstableImBtc",
        "native.mstableFpMbtcHbtc",
    ]

    badgerBoost = {}
    for name, sett in allSetts.items():
        if name in noBoost:
            continue
        balances = calculate_sett_balances(badger, name, currentBlock)
        balances = convert_balances_to_usd(sett, name, balances)
        if name in ["native.uniDiggWbtc", "native.sushiDiggWbtc", "native.digg"]:
            diggSetts = combine_balances([diggSetts, balances])
        elif name in [
            "native.badger",
            "native.uniBadgerWbtc",
            "native.sushiBadgerWbtc",
        ]:
            badgerSetts = combine_balances([badgerSetts, balances])
        else:
            nonNativeSetts = combine_balances([nonNativeSetts, balances])

    sharesPerFragment = badger.digg.logic.UFragments._sharesPerFragment()
    badger_wallet_balances, digg_wallet_balances, _ = fetch_wallet_balances(
        sharesPerFragment, currentBlock
    )

    console.log(
        "{} Badger balances fetched, {} Digg balances fetched".format(
            len(badger_wallet_balances), len(digg_wallet_balances)
        )
    )
    badger_wallet_balances = UserBalances(
        [
            UserBalance(addr, bal * prices[BADGER], BADGER)
            for addr, bal in badger_wallet_balances.items()
        ]
    )

    digg_wallet_balances = UserBalances(
        [
            UserBalance(addr, bal * prices[DIGG], DIGG)
            for addr, bal in digg_wallet_balances.items()
        ]
    )
    badgerSetts = filter_dust(combine_balances([badgerSetts, badger_wallet_balances]))
    diggSetts = filter_dust(combine_balances([diggSetts, digg_wallet_balances]))
    allAddresses = calc_union_addresses(diggSetts, badgerSetts, nonNativeSetts)

    console.log("Non native Setts before filter {}".format(len(nonNativeSetts)))
    nonNativeSetts = filter_dust(nonNativeSetts)
    console.log("Non native Setts after filter {}".format(len(nonNativeSetts)))

    console.log("Filtered balances < $1")

    console.log(
        "{} addresses collected for boost calculation".format(len(allAddresses))
    )
    stakeRatiosList = [
        calc_stake_ratio(addr, diggSetts, badgerSetts, nonNativeSetts)
        for addr in allAddresses
    ]
    stakeRatios = dict(zip(allAddresses, stakeRatiosList))
    stakeRatios = OrderedDict(
        sorted(stakeRatios.items(), key=lambda t: t[1], reverse=True)
    )

    for addr in allAddresses:
        boostInfo[addr.lower()] = {
            "nativeBalance": 0,
            "nonNativeBalance": 0,
            "stakeRatio": 0,
        }

    for user in badgerSetts:
        boostInfo[user.address.lower()]["nativeBalance"] += user.balance

    for user in diggSetts:
        boostInfo[user.address.lower()]["nativeBalance"] += user.balance

    for user in nonNativeSetts:
        boostInfo[user.address.lower()]["nonNativeBalance"] += user.balance

    for addr, ratio in stakeRatios.items():
        boostInfo[addr.lower()]["stakeRatio"] = ratio

    stakeData = {}
    console.log(STAKE_RATIO_RANGES)
    for addr, stakeRatio in stakeRatios.items():
        if stakeRatio == 0:
            badgerBoost[addr] = 1
        else:

            userBoost = 1
            userStakeRange = 0
            for stakeRange, multiplier in STAKE_RATIO_RANGES:
                if stakeRatio > stakeRange:
                    userBoost = multiplier
                    userStakeRange = stakeRange

            stakeData[userStakeRange] = stakeData.get(userStakeRange, 0) + 1
            badgerBoost[addr] = userBoost

    console.log(len(badgerBoost))
    print(
        tabulate(
            [[rng, amount] for rng, amount in stakeData.items()],
            headers=["range", "amount of users"],
        )
    )

    return badgerBoost, boostInfo

def main():
    # neeed to connect badger here
    badger = "something"
    currentBlock = 
    pass