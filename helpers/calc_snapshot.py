from classes.DiggUtils import diggUtils
from classes.RewardsList import RewardsList
from classes.RewardsLog import rewardsLog
from classes.Schedule import Schedule

from helpers.constants import (
    BADGER_TREE,
    DIGG,
    DFD,
    NON_NATIVE_SETTS,
)

from brownie import web3
from rich.console import Console


console = Console()

def parse_schedules(schedules):
    schedulesByToken = {}
    for s in schedules:
        schedule = Schedule(s[0], s[1], s[2], s[3], s[4], s[5])
        if schedule.token not in schedulesByToken:
            schedulesByToken[schedule.token] = []
        schedulesByToken[schedule.token].append(schedule)
    return schedulesByToken

def calc_snapshot(
    badger, name, startBlock, endBlock, nextCycle, boosts, unclaimedBalances
):
    console.log("==== Processing rewards for {} at {} ====".format(name, endBlock))

    rewards = RewardsList(nextCycle, badger.badgerTree)

    sett = badger.getSett(name)
    startTime = web3.eth.getBlock(startBlock)["timestamp"]

    endTime = web3.eth.getBlock(endBlock)["timestamp"]

    userBalances = calculate_sett_balances(badger, name, endBlock)

    apyBoosts = {}
    if name in NON_NATIVE_SETTS:
        console.log(
            "{} users out of {} boosted in {}".format(
                len(userBalances), len(boosts), name
            )
        )
        preBoost = {}
        for user in userBalances:
            preBoost[user.address] = userBalances.percentage_of_total(user.address)

        for user in userBalances:
            boostAmount = boosts.get(user.address, 1)
            user.boost_balance(boostAmount)

        for user in userBalances:
            postBoost = userBalances.percentage_of_total(user.address)
            apyBoosts[user.address] = postBoost / preBoost[user.address]

    schedulesByToken = parse_schedules(
        badger.rewardsLogger.getAllUnlockSchedulesFor(sett)
    )

    rewardsLog.add_schedules_in_range(
        sett.address, schedulesByToken, startTime, endTime
    )

    for token, schedules in schedulesByToken.items():
        endDist = get_distributed_for_token_at(token, endTime, schedules, name)
        startDist = get_distributed_for_token_at(token, startTime, schedules, name)
        tokenDistribution = int(endDist) - int(startDist)
        # Distribute to users with rewards list
        # Make sure there are tokens to distribute (some geysers only
        # distribute one token)
        if token == DIGG:
            fragments = diggUtils.sharesToFragments(tokenDistribution) / 1e9
            console.log("{} DIGG tokens distributed".format(fragments))
            rewardsLog.add_total_token_dist(name, token, fragments)
        elif token == DFD:
            console.log("{} DFD tokens distributed".format(tokenDistribution / 1e18))
            rewardsLog.add_total_token_dist(name, token, tokenDistribution / 1e18)
        else:
            badgerAmount = tokenDistribution / 1e18
            console.log("{} Badger token distributed".format(badgerAmount))
            rewardsLog.add_total_token_dist(name, token, tokenDistribution / 1e18)

        if tokenDistribution > 0:
            sumBalances = sum([b.balance for b in userBalances])
            rewardsUnit = tokenDistribution / sumBalances
            totalRewards = 0
            console.log("Processing rewards for {} addresses".format(len(userBalances)))
            for user in userBalances:
                addr = web3.toChecksumAddress(user.address)

                token = web3.toChecksumAddress(token)
                rewardAmount = user.balance * rewardsUnit
                totalRewards += rewardAmount
                ## If giving rewards to tree , distribute them to users with unlcaimed bals
                if addr == BADGER_TREE:
                    if name == "native.cvx":
                        console.log(
                            "Distributing {} rewards to {} unclaimed bCvx holders".format(
                                rewardAmount / 1e18, len(unclaimedBalances["bCvx"])
                            )
                        )
                        totalbCvxBal = sum(unclaimedBalances["bCvx"].values())
                        cvxRewardsUnit = rewardAmount / totalbCvxBal
                        for addr, bal in unclaimedBalances["bCvx"].items():
                            rewards.increase_user_rewards(
                                web3.toChecksumAddress(addr),
                                token,
                                int(cvxRewardsUnit * bal),
                            )
                    if name == "native.cvxCrv":

                        console.log(
                            "Distributing {} rewards to {} unclaimed bCvxCrv holders".format(
                                rewardAmount / 1e18, len(unclaimedBalances["bCvxCrv"])
                            )
                        )

                        totalbCvxCrvBal = sum(unclaimedBalances["bCvxCrv"].values())
                        bCvxCrvRewardsUnit = rewardAmount / totalbCvxCrvBal
                        for addr, bal in unclaimedBalances["bCvxCrv"].items():
                            rewards.increase_user_rewards(
                                web3.toChecksumAddress(addr),
                                token,
                                int(bCvxCrvRewardsUnit * bal),
                            )
                else:
                    rewards.increase_user_rewards(addr, token, int(rewardAmount))

            console.log(
                "Token Distribution: {}\nRewards Released: {}".format(
                    tokenDistribution / 1e18, totalRewards / 1e18
                )
            )
            console.log("Diff {}\n\n".format((abs(tokenDistribution - totalRewards))))

    return rewards, apyBoosts