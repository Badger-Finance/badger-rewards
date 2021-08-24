from helpers.web3_utils import make_contract
from rewards.rewards_utils import combine_rewards
from rewards.snapshot.chain_snapshot import sett_snapshot
from subgraph.client import fetch_tree_distributions
from rewards.classes.RewardsList import RewardsList
from helpers.time_utils import to_utc_date, to_hours
from config.env_config import env_config
from rich.console import Console
from typing import List

console = Console()


class RewardsManager:
    def __init__(self, chain: str, cycle: int, start: int, end: int):
        self.chain = chain
        self.web3 = env_config.get_web3(chain)
        self.cycle = cycle
        self.start = int(start)
        self.end = int(end)
        self.apyBoosts = {}

    def fetch_sett_snapshot(self, block: int, sett: str):
        return sett_snapshot(self.chain, block, sett)

    def get_sett_from_strategy(self, strat: str):
        strategy = make_contract(strat, "BaseStrategy", self.chain)
        controller = make_contract(
            strategy.functions.controller().call(), "Controller", self.chain
        )
        want = strategy.functions.want().call()
        sett = controller.functions.vaults(want).call()
        console.log(sett)
        return sett

    def calculate_sett_rewards(self, sett, schedulesByToken, boosts):
        startTime = self.web3.eth.getBlock(self.start)["timestamp"]
        endTime = self.web3.eth.getBlock(self.end)["timestamp"]
        rewards = RewardsList(self.cycle)
        settBalances = self.fetch_sett_snapshot(self.end, sett)
        boostedSettBalances = self.boost_sett(boosts, sett, settBalances)

        for token, schedules in schedulesByToken.items():
            endDist = self.get_distributed_for_token_at(token, endTime, schedules)
            startDist = self.get_distributed_for_token_at(token, startTime, schedules)
            tokenDistribution = int(endDist) - int(startDist)
            if tokenDistribution > 0:
                total = sum([b.balance for b in boostedSettBalances])
                rewardsUnit = tokenDistribution / total
                for user in boostedSettBalances:
                    addr = self.web3.toChecksumAddress(user.address)
                    token = self.web3.toChecksumAddress(token)
                    rewardAmount = user.balance * rewardsUnit
                    rewards.increase_user_rewards(
                        self.web3.toChecksumAddress(addr),
                        self.web3.toChecksumAddress(token),
                        int(rewardAmount),
                    )
        return rewards

    def calculate_all_sett_rewards(self, setts: List[str], allSchedules, boosts):
        allRewards = []
        for sett in setts:
            token = make_contract(sett, "ERC20", self.chain)
            console.log(
                "Calculating rewards for {}".format(token.functions.name().call())
            )
            allRewards.append(
                self.calculate_sett_rewards(sett, allSchedules[sett], boosts)
            )

        return combine_rewards(allRewards, self.cycle + 1)

    def get_distributed_for_token_at(self, token, endTime, schedules):
        totalToDistribute = 0
        for index, schedule in enumerate(schedules):
            if endTime < schedule.startTime:
                toDistribute = 0
                console.log("\nSchedule {} for {} completed\n".format(index, token))
            else:
                rangeDuration = endTime - schedule.startTime
                toDistribute = min(
                    schedule.initialTokensLocked,
                    int(
                        schedule.initialTokensLocked
                        * rangeDuration
                        // schedule.duration
                    ),
                )
                if schedule.startTime <= endTime and schedule.endTime >= endTime:
                    console.log(
                        "Tokens distributed by schedule {} at {} are {}% of total\n".format(
                            index,
                            to_utc_date(schedule.startTime),
                            (
                                int(toDistribute)
                                / int(schedule.initialTokensLocked)
                                * 100
                            ),
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

    def boost_sett(self, boosts, sett, snapshot):
        if snapshot.settType == "nonNative":
            preBoost = {}
            for user in snapshot:
                preBoost[user.address] = snapshot.percentage_of_total(user.address)

            for user in snapshot:
                boostInfo = boosts.get(user.address, {})
                boost = boostInfo.get("boost", 1)
                user.boost_balance(boost)

            for user in snapshot:
                postBoost = snapshot.percentage_of_total(user.address)
                if sett not in self.apyBoosts:
                    self.apyBoosts[sett] = {}

                self.apyBoosts[sett][user.address] = postBoost / preBoost[user.address]
        return snapshot

    def calculate_tree_distributions(self):
        treeDistributions = fetch_tree_distributions(self.start, self.end, self.chain)
        console.log(
            "Fetched {} tree distributions between {} and {}".format(
                len(treeDistributions), self.start, self.end
            )
        )
        rewards = RewardsList(self.cycle + 1)
        for dist in treeDistributions:
            console.log(dist)
            block = int(dist["blockNumber"])
            token = dist["token"]["address"]
            strategy = dist["id"].split("-")[0]
            sett = self.get_sett_from_strategy(strategy)
            balances = self.fetch_sett_snapshot(block, sett)
            amount = int(dist["amount"])
            rewardsUnit = amount / sum([u.balance for u in balances])
            for user in balances:
                userRewards = rewardsUnit * user.balance
                rewards.increase_user_rewards(
                    self.web3.toChecksumAddress(user.address),
                    self.web3.toChecksumAddress(token),
                    int(userRewards),
                )
        return rewards

    def calc_sushi_distributions(self):
        pass
