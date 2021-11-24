from decimal import Decimal
from typing import Dict, List, Tuple

from rich.console import Console

from badger_api.requests import fetch_token
from config.singletons import env_config
from helpers.constants import EMISSIONS_CONTRACTS, XSUSHI
from helpers.discord import get_discord_url, send_message_to_discord
from helpers.enums import BalanceType, Network
from helpers.time_utils import to_hours, to_utc_date
from helpers.web3_utils import make_contract
from rewards.classes.CycleLogger import cycle_logger
from rewards.classes.RewardsList import RewardsList
from rewards.classes.Schedule import Schedule
from rewards.classes.Snapshot import Snapshot
from rewards.emission_handlers import eth_tree_handler
from rewards.explorer import get_block_by_timestamp
from rewards.snapshot.chain_snapshot import sett_snapshot
from rewards.utils.emission_utils import get_flat_emission_rate
from rewards.utils.rewards_utils import combine_rewards, distribute_rewards_to_snapshot
from subgraph.queries.harvests import (
    fetch_sushi_harvest_events,
    fetch_tree_distributions,
)

console = Console()


class RewardsManager:
    def __init__(self, chain: str, cycle: int, start: int, end: int, boosts):
        self.chain = chain
        self.web3 = env_config.get_web3(chain)
        self.discord_url = get_discord_url(chain)
        self.cycle = cycle
        self.start = int(start)
        self.end = int(end)
        self.boosts = boosts
        self.apy_boosts = {}

    def fetch_sett_snapshot(
        self, block: int, sett: str, blacklist: bool = True
    ) -> Snapshot:
        return sett_snapshot(self.chain, block, sett, blacklist)

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
        start_time = self.web3.eth.get_block(self.start)["timestamp"]
        end_time = self.web3.eth.get_block(self.end)["timestamp"]
        sett_snapshot = self.fetch_sett_snapshot(self.end, sett)

        """
        Vaults can have a split of boosted and non boosted emissions
        which are calculated using the boosted balances and the normal
        balances respectively
        
        """
        flat_rewards_list = []
        boosted_rewards_list = []
        custom_behaviour = {}

        for token, schedules in schedules_by_token.items():
            end_dist = self.get_distributed_for_token_at(token, end_time, schedules)
            start_dist = self.get_distributed_for_token_at(token, start_time, schedules)
            token_distribution = end_dist - start_dist
            emissions_rate = get_flat_emission_rate(sett, self.chain)
            flat_emissions = token_distribution * emissions_rate
            boosted_emissions = token_distribution * (1 - emissions_rate)
            if flat_emissions > 0:
                flat_rewards_list.append(
                    distribute_rewards_to_snapshot(
                        amount=flat_emissions,
                        snapshot=sett_snapshot,
                        token=token,
                        custom_rewards=custom_behaviour,
                    )
                )
            if boosted_emissions > 0:
                boosted_rewards_list.append(
                    distribute_rewards_to_snapshot(
                        boosted_emissions,
                        snapshot=self.boost_sett(sett, sett_snapshot),
                        token=token,
                        custom_rewards=custom_behaviour,
                    )
                )

        flat_rewards = combine_rewards(flat_rewards_list, self.cycle)
        boosted_rewards = combine_rewards(boosted_rewards_list, self.cycle)

        return (
            combine_rewards([flat_rewards, boosted_rewards], self.cycle),
            flat_rewards,
            boosted_rewards,
        )

    def calculate_all_sett_rewards(
        self, setts: List[str], all_schedules: Dict[str, Dict[str, List[Schedule]]]
    ) -> RewardsList:
        all_rewards = []
        for sett in setts:
            token = make_contract(sett, "ERC20", self.chain)
            console.log(f"Calculating rewards for {token.name().call()}")
            rewards, flat, boosted = self.calculate_sett_rewards(
                sett, all_schedules[sett]
            )
            desc = f"**Boosted Rewards**\n\n{boosted.totals_info(self.chain)}\n\n**Flat Rewards**\n\n{flat.totals_info(self.chain)}"
            sett_token = fetch_token(self.chain, sett)
            sett_name = sett_token.get("name", "")
            send_message_to_discord(
                f"Rewards for {sett_name}",
                description=desc,
                fields=[],
                username="Rewards Bot",
                url=self.discord_url,
            )
            all_rewards.append(rewards)

        return combine_rewards(all_rewards, self.cycle)

    def get_sett_multipliers(self) -> Dict[str, Dict[str, float]]:
        sett_multipliers = {}
        for sett, user_apy_boosts in self.apy_boosts.items():
            sett_multipliers[sett] = {
                "min": float(min(user_apy_boosts.values())),
                "max": float(max(user_apy_boosts.values())),
            }
        return sett_multipliers

    def get_user_multipliers(self) -> Dict[str, Dict[str, float]]:
        user_multipliers = {}
        for sett, multipliers in self.get_sett_multipliers().items():
            min_mult = multipliers["min"]
            max_mult = multipliers["max"]
            diff = float(max_mult - min_mult)
            for user, boost_info in self.boosts.items():
                if user not in user_multipliers:
                    user_multipliers[user] = {}
                boost = boost_info.get("boost", 1)
                if boost == 1:
                    user_sett_multiplier = min_mult
                else:
                    user_sett_multiplier = min_mult + (boost / 2000) * diff
                user_multipliers[user][sett] = user_sett_multiplier

        return user_multipliers

    def get_distributed_for_token_at(
        self, token: str, end_time: int, schedules: List[Schedule]
    ) -> Decimal:
        total_to_distribute = Decimal(0)
        for index, schedule in enumerate(schedules):
            if end_time < schedule.startTime:
                to_distribute = Decimal(0)
                console.log(f"\nSchedule {index} for {token} completed\n")
            else:
                range_duration = end_time - schedule.startTime
                if schedule.initialTokensLocked == 0:
                    to_distribute = Decimal(0)
                else:
                    to_distribute = Decimal(
                        min(
                            schedule.initialTokensLocked,
                            int(
                                schedule.initialTokensLocked
                                * range_duration
                                // schedule.duration
                            ),
                        )
                    )
                if schedule.startTime <= end_time and schedule.endTime >= end_time:
                    percentage_out_of_total = (
                        (int(to_distribute) / int(schedule.initialTokensLocked) * 100)
                        if int(schedule.initialTokensLocked) > 0
                        else 0
                    )
                    percentage_total_duration = (
                        (range_duration / schedule.duration * 100)
                        if schedule.duration > 0
                        else 0
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
                        f" or {percentage_total_duration}% of total duration.",
                    )
            total_to_distribute += to_distribute

        return total_to_distribute

    def boost_sett(self, sett: str, snapshot: Snapshot) -> Snapshot:
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
            self.web3.eth.get_block(self.start)["timestamp"],
            self.web3.eth.get_block(self.end)["timestamp"],
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
                distribute_rewards_to_snapshot(amount, snapshot, token)
            )
        return combine_rewards(all_dist_rewards, self.cycle)

    def calc_sushi_distributions(self) -> RewardsList:
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

    def calc_sushi_distribution(
        self, strategy: str, events: List[Dict]
    ) -> Tuple[RewardsList, int]:
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
            cycle_logger.add_sett_token_data(sett, XSUSHI, reward_amount)
            total_from_rewards += reward_amount
            cycle_logger.add_sett_token_data(
                sett, self.web3.toChecksumAddress(XSUSHI), reward_amount
            )

            snapshot = self.fetch_sett_snapshot(block, sett)
            all_sushi_rewards.append(
                distribute_rewards_to_snapshot(reward_amount, snapshot, XSUSHI)
            )

        return combine_rewards(all_sushi_rewards, self.cycle), total_from_rewards
