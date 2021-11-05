from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.classes.Snapshot import Snapshot
from helpers.constants import (
    BCVX,
    BCVXCRV,
    PRO_RATA_VAULTS,
    XSUSHI,
    EMISSIONS_CONTRACTS,
    DIGG,
)
from rewards.explorer import get_block_by_timestamp
from helpers.web3_utils import make_contract
from rewards.rewards_utils import combine_rewards
from rewards.snapshot.chain_snapshot import sett_snapshot
from subgraph.queries.harvests import (
    fetch_sushi_harvest_events,
    fetch_tree_distributions,
)
from rewards.classes.RewardsList import RewardsList
from rewards.classes.Schedule import Schedule
from rewards.classes.CycleLogger import cycle_logger
from helpers.time_utils import to_utc_date, to_hours
from helpers.digg_utils import digg_utils
from helpers.enums import BalanceType, Network
from config.env_config import env_config
from rich.console import Console
from typing import List, Tuple, Dict

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

    def fetch_sett_snapshot(
        self, block: int, sett: str, blacklist: bool = True
    ) -> Snapshot:
        return sett_snapshot(self.chain, block, sett, blacklist)

    def bcvx_claims_snapshot(self):
        bcvx = claims_snapshot()[BCVX]
        console.log(bcvx)
        return bcvx

    def bcvxcrv_claims_snapshot(self):
        bcvxcrv = claims_snapshot()[BCVXCRV]
        console.log(bcvxcrv)
        return bcvxcrv

    def get_sett_from_strategy(self, strat: str) -> str:
        """Go from strategy -> want -> controller -> want -> sett

        :param strat: Strategy to find sett of
        :type strat: str
        :rtype: str
        """
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
        sett_snapshot = self.fetch_sett_snapshot(self.end, sett)
        rewards = RewardsList(self.cycle)
        extra_rewards = []
        """
        When distributing rewards to the bcvx vault,
        we want them to be calculated pro-rata
        rather than boosted
        """
        if self.web3.toChecksumAddress(sett) not in PRO_RATA_VAULTS:
            sett_snapshot = self.boost_sett(sett, sett_snapshot)

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
                sett = self.web3.toChecksumAddress(sett)
                total = sett_snapshot.total_balance()
                if total == 0:
                    unit = 0
                else:
                    unit = token_distribution / total
                    for user, balance in sett_snapshot:
                        addr = self.web3.toChecksumAddress(user)
                        token = self.web3.toChecksumAddress(token)
                        reward_amount = balance * unit
                        if addr == EMISSIONS_CONTRACTS[Network.Ethereum]["BadgerTree"]:
                            if sett == BCVX:
                                extra_rewards.append(
                                    self.distribute_rewards_to_snapshot(
                                        reward_amount,
                                        self.bcvx_claims_snapshot(),
                                        token,
                                    )
                                )
                                console.log(
                                    f"{reward_amount} distributed to bcvxcrv holders"
                                )

                            if sett == BCVXCRV:

                                extra_rewards.append(
                                    self.distribute_rewards_to_snapshot(
                                        reward_amount,
                                        self.bcvxcrv_claims_snapshot(),
                                        token,
                                    )
                                )
                                console.log(
                                    f"{reward_amount} distributed to bcvxcrv holders"
                                )
                        else:
                            rewards.increase_user_rewards(
                                addr, token, int(reward_amount)
                            )

        return combine_rewards([rewards, *extra_rewards], self.cycle)

    def distribute_rewards_to_snapshot(
        self, amount: float, snapshot: Snapshot, token: str
    ):
        """
        Distribute a certain amount of rewards to a snapshot of users
        """
        rewards = RewardsList(self.cycle)
        total = snapshot.total_balance()
        if total == 0:
            unit = 0
        else:
            unit = amount / total
        for user, balance in snapshot:
            addr = self.web3.toChecksumAddress(user)
            token = self.web3.toChecksumAddress(token)
            reward_amount = balance * unit
            assert reward_amount >= 0
            rewards.increase_user_rewards(addr, token, int(reward_amount))
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

    def boost_sett(self, sett: str, snapshot: Snapshot):
        if snapshot.type == BalanceType.NonNative:
            pre_boost = {}
            for user, balance in snapshot:
                pre_boost[user] = snapshot.percentage_of_total(user)

            for user, balance in snapshot:
                boost_info = self.boosts.get(user, {})
                boost = boost_info.get("boost", 1)
                snapshot.boost_balance(user, boost)

            for user, balance in snapshot:
                post_boost = snapshot.percentage_of_total(user)
                if sett not in self.apy_boosts:
                    self.apy_boosts[sett] = {}

                self.apy_boosts[sett][user] = post_boost / pre_boost[user]

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
        all_dist_rewards = []
        for dist in tree_distributions:
            block = get_block_by_timestamp(self.chain, int(dist["timestamp"]))
            token = dist["token"]["address"]
            strategy = dist["id"].split("-")[0]
            sett = self.get_sett_from_strategy(strategy)
            # Dont blacklist tree rewards for emissions contracts
            snapshot = self.fetch_sett_snapshot(block, sett, blacklist=False)
            amount = int(dist["amount"])

            cycle_logger.add_tree_distribution(sett, dist)
            cycle_logger.add_sett_token_data(
                sett, self.web3.toChecksumAddress(token), amount
            )
            all_dist_rewards.append(
                self.distribute_rewards_to_snapshot(amount, snapshot, token)
            )
        return combine_rewards(all_dist_rewards, self.cycle)

    def calc_sushi_distributions(self) -> Tuple[RewardsList, float]:
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

    def calc_sushi_distribution(self, strategy: str, events):
        sett = self.get_sett_from_strategy(strategy)
        total_from_rewards = 0
        all_sushi_rewards = []
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
            total_from_rewards += reward_amount
            cycle_logger.add_sett_token_data(
                sett, self.web3.toChecksumAddress(XSUSHI), reward_amount
            )
            snapshot = self.fetch_sett_snapshot(block, sett)
            all_sushi_rewards.append(
                self.distribute_rewards_to_snapshot(reward_amount, snapshot, XSUSHI)
            )

        return combine_rewards(all_sushi_rewards, self.cycle), total_from_rewards
