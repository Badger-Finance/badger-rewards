from helpers.constants import XSUSHI
from helpers.web3_utils import make_contract
from rewards.rewards_utils import combine_rewards
from rewards.snapshot.chain_snapshot import sett_snapshot
from subgraph.queries.harvests import (
    fetch_sushi_harvest_events,
    fetch_tree_distributions,
)
from rewards.classes.RewardsList import RewardsList
from rewards.classes.Schedule import Schedule
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

    def get_sett_from_strategy(self, strat: str) -> str:
        strategy = make_contract(strat, "BaseStrategy", self.chain)
        controller = make_contract(
            strategy.controller().call(), "Controller", self.chain
        )
        want = strategy.want().call()
        sett = controller.vaults(want).call()
        return sett

    def calculate_sett_rewards(self, sett, schedulesByToken, boosts) -> RewardsList:
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
                total = boostedSettBalances.total_balance()
                rewardsUnit = tokenDistribution / total
                for user in boostedSettBalances:
                    addr = self.web3.toChecksumAddress(user.address)
                    token = self.web3.toChecksumAddress(token)
                    rewardAmount = user.balance * rewardsUnit
                    assert rewardAmount > 0
                    rewards.increase_user_rewards(
                        self.web3.toChecksumAddress(addr),
                        self.web3.toChecksumAddress(token),
                        int(rewardAmount),
                    )
        return rewards

    def calculate_all_sett_rewards(
        self, setts: List[str], allSchedules, boosts
    ) -> RewardsList:
        all_rewards = []
        for sett in setts:
            token = make_contract(sett, "ERC20", self.chain)
            console.log("Calculating rewards for {}".format(token.name().call()))
            all_rewards.append(
                self.calculate_sett_rewards(sett, allSchedules[sett], boosts)
            )

        return combine_rewards(all_rewards, self.cycle + 1)

    def get_sett_multipliers(self):
        settMultipliers = {}
        for sett, userApyBoosts in self.apyBoosts.items():
            settMultipliers[sett] = {
                "min": min(userApyBoosts.values()),
                "max": max(userApyBoosts.values()),
            }
        return settMultipliers

    def get_user_multipliers(self):
        userMultipliers = {}
        for sett, userApyMultipliers in self.apyBoosts.items():
            for user, apyMultiplier in userApyMultipliers.items():
                user = self.web3.toChecksumAddress(user)
                if user not in userMultipliers:
                    userMultipliers[user] = {}
                userMultipliers[user][sett] = apyMultiplier
        return userMultipliers

    def get_distributed_for_token_at(
        self, token: str, endTime: int, schedules: List[Schedule]
    ) -> float:
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

    def calculate_tree_distributions(self) -> RewardsList:
        tree_distributions = fetch_tree_distributions(self.start, self.end, self.chain)
        console.log(
            "Fetched {} tree distributions between {} and {}".format(
                len(tree_distributions), self.start, self.end
            )
        )
        rewards = RewardsList(self.cycle)
        for dist in tree_distributions:
            console.log(dist)
            block = int(dist["blockNumber"])
            token = dist["token"]["address"]
            strategy = dist["id"].split("-")[0]
            sett = self.get_sett_from_strategy(strategy)
            balances = self.fetch_sett_snapshot(block, sett)
            amount = int(dist["amount"])
            rewards_unit = amount / balances.total_balance()
            for user in balances:
                user_rewards = rewards_unit * user.balance
                rewards.increase_user_rewards(
                    self.web3.toChecksumAddress(user.address),
                    self.web3.toChecksumAddress(token),
                    int(user_rewards),
                )
        return rewards

    def calc_sushi_distributions(self):
        sushi_events = fetch_sushi_harvest_events(self.start, self.end)
        all_from_events = 0
        all_sushi_rewards = []
        all_from_rewards = 0
        for strategy, events in sushi_events.items():
            rewards, from_rewards = self.calc_sushi_distribution(strategy, events)
            all_from_events += sum(map(lambda e: int(e["rewardAmount"]), events))
            all_from_rewards += from_rewards
            all_sushi_rewards.append(rewards)
        assert abs(all_from_events - all_from_rewards) < 1e9
        return combine_rewards(all_sushi_rewards, self.cycle)

    def calc_sushi_distribution(self, strategy, events):
        sett = self.get_sett_from_strategy(strategy)
        rewards = RewardsList(self.cycle)
        total_from_rewards = 0

        for event in events:
            block = int(event["blockNumber"])
            reward_amount = int(event["rewardAmount"])
            balances = self.fetch_sett_snapshot(block, sett)
            rewards_unit = reward_amount / balances.total_balance()
            for user in balances:
                user_rewards = rewards_unit * user.balance
                total_from_rewards += user_rewards
                rewards.increase_user_rewards(
                    self.web3.toChecksumAddress(user.address),
                    self.web3.toChecksumAddress(XSUSHI),
                    int(user_rewards),
                )
        return rewards, total_from_rewards
