from helpers.constants import PRO_RATA_VAULTS, XSUSHI
from rewards.explorer import get_block_by_timestamp
from helpers.web3_utils import make_contract
from rewards.rewards_utils import combine_rewards
from rewards.snapshot.chain_snapshot import sett_snapshot
from subgraph.queries.harvests import (
    fetch_sushi_harvest_events,
    fetch_tree_distributions,
)
from rewards.classes.RewardsList import RewardsList
from rewards.classes.UserBalance import UserBalances
from rewards.classes.Schedule import Schedule
from rewards.classes.CycleLogger import cycle_logger
from helpers.time_utils import to_utc_date, to_hours
from helpers.constants import DIGG
from helpers.digg_utils import digg_utils
from config.env_config import env_config
from rich.console import Console
from typing import List, Dict

console = Console()


class RewardsManager:
    def __init__(self, chain: str, cycle: int, start: int, end: int, boosts):
        self.chain = chain
        self.web3 = env_config.get_web3(chain)
        self.cycle = cycle
        self.start = int(start)
        self.end = int(end)
        self.boosts = boosts
        self.apy_boosts = {}

    def fetch_sett_snapshot(self, block: int, sett: str, blacklist: bool = True):
        return sett_snapshot(self.chain, block, sett, blacklist)

    def get_sett_from_strategy(self, strat: str) -> str:
        strategy = make_contract(strat, "BaseStrategy", self.chain)
        controller = make_contract(
            strategy.controller().call(), "Controller", self.chain
        )
        want = strategy.want().call()
        sett = controller.vaults(want).call()
        return sett

    def calculate_sett_rewards(
        self, sett: str, schedules_by_token: Dict[str, List[Schedule]]
    ) -> RewardsList:
        start_time = self.web3.eth.getBlock(self.start)["timestamp"]
        end_time = self.web3.eth.getBlock(self.end)["timestamp"]
        rewards = RewardsList(self.cycle)
        sett_balances = self.fetch_sett_snapshot(self.end, sett)

        """
        When distributing rewards to the bcvx vault,
        we want them to be calculated pro-rata
        rather than boosted
        """
        if self.web3.toChecksumAddress(sett) not in PRO_RATA_VAULTS:
            sett_balances = self.boost_sett(sett, sett_balances)

        for token, schedules in schedules_by_token.items():
            token = self.web3.toChecksumAddress(token)
            end_dist = self.get_distributed_for_token_at(
                token, end_time, schedules, sett
            )
            start_dist = self.get_distributed_for_token_at(
                token, start_time, schedules, sett
            )
            for schedule in schedules:
                if schedule.startTime <= end_time and schedule.endTime >= end_time:
                    cycle_logger.add_schedule(sett, schedule)

            token_distribution = int(end_dist) - int(start_dist)
            if token == DIGG:
                cycle_logger.add_sett_token_data(
                    sett, token, digg_utils.shares_to_fragments(token_distribution)
                )
            else:
                cycle_logger.add_sett_token_data(sett, token, token_distribution)

            if token_distribution > 0:
                total = sett_balances.total_balance()
                rewards_unit = token_distribution / total
                for user in sett_balances:
                    addr = self.web3.toChecksumAddress(user.address)
                    reward_amount = user.balance * rewards_unit
                    assert reward_amount >= 0
                    rewards.increase_user_rewards(
                        self.web3.toChecksumAddress(addr),
                        self.web3.toChecksumAddress(token),
                        int(reward_amount),
                    )
        return rewards

    def calculate_all_sett_rewards(
        self, setts: List[str], all_schedules: Dict[str, Dict[str, List[Schedule]]]
    ) -> RewardsList:
        all_rewards = []
        for sett in setts:
            token = make_contract(sett, "ERC20", self.chain)

            console.log(f"Calculating rewards for {token.name().call()}")
            all_rewards.append(self.calculate_sett_rewards(sett, all_schedules[sett]))

        return combine_rewards(all_rewards, self.cycle + 1)

    def get_sett_multipliers(self):
        sett_multipliers = {}
        for sett, user_apy_boosts in self.apy_boosts.items():
            sett_multipliers[sett] = {
                "min": min(user_apy_boosts.values()),
                "max": max(user_apy_boosts.values()),
            }
        return sett_multipliers

    def get_user_multipliers(self) -> Dict[str, Dict[str, float]]:
        user_multipliers = {}
        for sett, multipliers in self.get_sett_multipliers().items():
            min_mult = multipliers["min"]
            max_mult = multipliers["max"]
            diff = max_mult - min_mult
            for user, boost_info in self.boosts.items():
                if user not in user_multipliers:
                    user_multipliers[user] = {}
                boost = boost_info.get("boost", 1)
                if boost == 1:
                    user_sett_multiplier = multipliers["min"]
                else:
                    user_sett_multiplier = multipliers["min"] + (boost / 2000) * diff
                user_multipliers[user][sett] = user_sett_multiplier

        return user_multipliers

    def get_distributed_for_token_at(
        self, token: str, end_time: int, schedules: List[Schedule], sett: str
    ) -> float:
        total_to_distribute = 0
        for index, schedule in enumerate(schedules):
            if end_time < schedule.startTime:
                to_distribute = 0
                console.log(f"\nSchedule {index} for {token} completed\n")
            else:
                range_duration = end_time - schedule.startTime
                if schedule.initialTokensLocked == 0:
                    to_distribute = 0
                else:
                    to_distribute = min(
                        schedule.initialTokensLocked,
                        int(
                            schedule.initialTokensLocked
                            * range_duration
                            // schedule.duration
                        ),
                    )
                if schedule.startTime <= end_time and schedule.endTime >= end_time:
                    percentage_out_of_total = (
                        int(to_distribute) / int(schedule.initialTokensLocked) * 100
                    )
                    console.log(
                        (
                            f"Token {token} distributed by schedule {index}"
                            f"at {to_utc_date(schedule.startTime)}"
                            f"are {percentage_out_of_total}% of total\n"
                        )
                    )

                    console.log(
                        f"Total duration of schedule elapsed is {to_hours(range_duration)}"
                        f" hours out of {to_hours(schedule.duration)} hours"
                        f" or {range_duration/schedule.duration * 100}% of total duration.",
                    )
            total_to_distribute += to_distribute

        return total_to_distribute

    def boost_sett(self, sett: str, snapshot: UserBalances):
        if snapshot.sett_type == "nonNative":
            pre_boost = {}
            for user in snapshot:
                pre_boost[user.address] = snapshot.percentage_of_total(user.address)

            for user in snapshot:
                boost_info = self.boosts.get(user.address, {})
                boost = boost_info.get("boost", 1)
                user.boost_balance(boost)

            for user in snapshot:
                post_boost = snapshot.percentage_of_total(user.address)
                if sett not in self.apy_boosts:
                    self.apy_boosts[sett] = {}

                self.apy_boosts[sett][user.address] = (
                    post_boost / pre_boost[user.address]
                )

        return snapshot

    def calculate_tree_distributions(self) -> RewardsList:
        tree_distributions = fetch_tree_distributions(
            self.web3.eth.getBlock(self.start)["timestamp"],
            self.web3.eth.getBlock(self.end)["timestamp"],
            self.chain,
        )
        console.log(
            f"Fetched {len(tree_distributions)} tree distributions between {self.start} and {self.end}"
        )
        rewards = RewardsList(self.cycle + 1)
        for dist in tree_distributions:
            block = get_block_by_timestamp(self.chain, int(dist["timestamp"]))
            token = dist["token"]["address"]
            strategy = dist["id"].split("-")[0]
            sett = self.get_sett_from_strategy(strategy)
            balances = self.fetch_sett_snapshot(block, sett, blacklist=False)
            amount = int(dist["amount"])
            total_balance = balances.total_balance()
            if total_balance == 0:
                rewards_unit = 0
            else:
                rewards_unit = amount / balances.total_balance()

            cycle_logger.add_tree_distribution(sett, dist)
            cycle_logger.add_sett_token_data(
                sett, self.web3.toChecksumAddress(token), amount
            )
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
            cycle_logger.add_tree_distribution(
                sett,
                {
                    "id": event["id"],
                    "blockNumber": event["blockNumber"],
                    "timestamp": event["timestamp"],
                    "token": {"address": XSUSHI, "symbol": "xSushi"},
                    "amount": event["rewardAmount"],
                },
            )
            block = int(event["blockNumber"])
            reward_amount = int(event["rewardAmount"])
            cycle_logger.add_sett_token_data(
                sett, self.web3.toChecksumAddress(XSUSHI), reward_amount
            )
            balances = self.fetch_sett_snapshot(block, sett, blacklist=False)
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
