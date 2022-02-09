from collections import defaultdict
from copy import deepcopy
from decimal import Decimal
from typing import Dict, List, Tuple

from rich.console import Console
from tabulate import tabulate

from badger_api.requests import fetch_token
from config.constants.addresses import ETH_BADGER_TREE, IBBTC_PEAK, FBVECVXLP, FBVECVX
from config.constants.chain_mappings import BOOSTED_EMISSION_TOKENS
from config.constants.emissions import (
    NUMBER_OF_HISTORICAL_SNAPSHOTS_FOR_SETT_REWARDS,
    NUMBER_OF_HISTORICAL_SNAPSHOTS_FOR_TREE_REWARDS,
)
from config.singletons import env_config
from helpers.discord import (
    get_discord_url,
    send_code_block_to_discord,
    send_plain_text_to_discord,
)
from helpers.enums import BalanceType, DiscordRoles, Network
from badger_utils.time_utils import seconds_to_hours, to_utc_date
from rewards.classes.RewardsList import RewardsList
from rewards.classes.Schedule import Schedule
from rewards.classes.Snapshot import Snapshot
from rewards.emission_handlers import fuse_pool_handler, ibbtc_peak_handler, unclaimed_rewards_handler
from rewards.explorer import get_block_by_timestamp
from rewards.snapshot.chain_snapshot import total_twap_sett_snapshot
from rewards.utils.emission_utils import get_flat_emission_rate
from rewards.utils.rewards_utils import (
    check_token_totals_in_range,
    combine_rewards,
    distribute_rewards_from_total_snapshot,
)
from subgraph.queries.harvests import fetch_tree_distributions

console = Console()


class RewardsManager:
    CUSTOM_BEHAVIOUR = {
        ETH_BADGER_TREE: unclaimed_rewards_handler,
        IBBTC_PEAK: ibbtc_peak_handler,
        FBVECVXLP: fuse_pool_handler,
        FBVECVX: fuse_pool_handler
    }

    def __init__(self, chain: Network, cycle: int, start: int, end: int, boosts):
        self.chain = chain
        self.web3 = env_config.get_web3(chain)
        self.discord_url = get_discord_url(chain)
        self.cycle = cycle
        self.start = int(start)
        self.end = int(end)
        self.boosts = boosts
        self.apy_boosts = {}

    def fetch_sett_snapshot(
        self, start_block: int, end_block: int, sett: str, blacklist: bool = True
    ) -> Snapshot:
        return total_twap_sett_snapshot(
            self.chain,
            start_block,
            end_block,
            sett,
            blacklist=blacklist,
            num_historical_snapshots=NUMBER_OF_HISTORICAL_SNAPSHOTS_FOR_SETT_REWARDS
        )

    def calculate_sett_rewards(
        self, sett: str, schedules_by_token: Dict[str, List[Schedule]]
    ) -> Tuple[RewardsList, RewardsList, RewardsList, Dict[str, Decimal]]:
        """
        Vaults can have a split of boosted and non boosted emissions
        which are calculated using the boosted balances and the normal
        balances respectively
        """
        start_time = self.web3.eth.get_block(self.start)["timestamp"]
        end_time = self.web3.eth.get_block(self.end)["timestamp"]
        snapshot = self.fetch_sett_snapshot(self.start, self.end, sett)
        flat_rewards_list = []
        boosted_rewards_list = []
        expected_distribution_amounts = {}

        for token, schedules in schedules_by_token.items():
            end_dist = self.get_distributed_for_token_at(token, end_time, schedules)
            start_dist = self.get_distributed_for_token_at(token, start_time, schedules)
            token_distribution = end_dist - start_dist
            expected_distribution_amounts[token] = token_distribution
            if token in BOOSTED_EMISSION_TOKENS.get(self.chain, []):
                emissions_rate = get_flat_emission_rate(sett, self.chain)
            else:
                emissions_rate = 1
            flat_emissions = token_distribution * emissions_rate
            boosted_emissions = token_distribution * (1 - emissions_rate)
            if flat_emissions > 0:
                flat_rewards_list.append(
                    distribute_rewards_from_total_snapshot(
                        amount=flat_emissions,
                        snapshot=snapshot,
                        token=token,
                        block=self.end,
                        custom_rewards=self.CUSTOM_BEHAVIOUR,
                    )
                )
            if boosted_emissions > 0:
                boosted_rewards_list.append(
                    distribute_rewards_from_total_snapshot(
                        boosted_emissions,
                        snapshot=self.boost_sett(sett, snapshot),
                        token=token,
                        block=self.end,
                        custom_rewards=self.CUSTOM_BEHAVIOUR,
                    )
                )

        flat_rewards = combine_rewards(flat_rewards_list, self.cycle)
        boosted_rewards = combine_rewards(boosted_rewards_list, self.cycle)

        return (
            combine_rewards([flat_rewards, boosted_rewards], self.cycle),
            flat_rewards,
            boosted_rewards,
            expected_distribution_amounts,
        )

    def calculate_all_sett_rewards(
        self, setts: List[str], all_schedules: Dict[str, Dict[str, List[Schedule]]]
    ) -> RewardsList:
        all_rewards = []
        table = []
        rewards_per_sett = defaultdict(dict)
        for sett in setts:
            sett_token = fetch_token(self.chain, sett)
            sett_name = sett_token.get("name", "")
            console.log(f"Calculating rewards for {sett_name}")
            rewards, flat, boosted, expected = self.calculate_sett_rewards(
                sett, all_schedules[sett]
            )
            table.append(
                [
                    sett_name,
                    boosted.totals_info(self.chain),
                    flat.totals_info(self.chain),
                ]
            )
            all_rewards.append(rewards)
            rewards_per_sett[sett]["actual"] = rewards.totals.toDict()
            rewards_per_sett[sett]["expected"] = expected
        
        send_code_block_to_discord(
            msg=tabulate(table, headers=["vault", "boosted rewards", "flat rewards"]),
            username="Rewards Bot",
            url=self.discord_url,
        )

        invalid_totals = check_token_totals_in_range(self.chain, rewards_per_sett)
        if len(invalid_totals):
            self.report_invalid_totals(invalid_totals)
            
        return combine_rewards(all_rewards, self.cycle)
    
    def report_invalid_totals(self, invalid_totals: List[List[str]]) -> None:
        send_plain_text_to_discord(
            msg=f"INCORRECT REWARDS DISTRIBTION {DiscordRoles.RewardsPod}",
            username="Rewards Bot",
            url=self.discord_url,
        )
        send_code_block_to_discord(
            msg=tabulate(invalid_totals, headers=["token", "min expected", "max expected", "actual"]),
            username="Rewards Bot",
            url=self.discord_url,
        )
        raise Exception(f"trying to distribute invalid reward amounts: {invalid_totals}")

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
                        f"Total duration of schedule elapsed is {seconds_to_hours(range_duration)}"
                        f" hours out of {seconds_to_hours(schedule.duration)} hours"
                        f" or {percentage_total_duration}% of total duration.",
                    )
            total_to_distribute += to_distribute

        return total_to_distribute

    def boost_sett(self, sett: str, snapshot: Snapshot) -> Snapshot:
        snapshot = deepcopy(snapshot)
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
            f"Fetched {len(tree_distributions)} "
            f"tree distributions between {self.start} and {self.end}"
        )
        all_dist_rewards = []

        for dist in tree_distributions:
            start_block = get_block_by_timestamp(
                self.chain, int(dist["end_of_previous_dist_timestamp"])
            )
            end_block = get_block_by_timestamp(self.chain, int(dist["timestamp"]))
            token = dist["token"]
            sett = dist["sett"]
            snapshot = total_twap_sett_snapshot(
                self.chain,
                start_block,
                end_block,
                sett,
                blacklist=False,
                num_historical_snapshots=NUMBER_OF_HISTORICAL_SNAPSHOTS_FOR_TREE_REWARDS
            )
            amount = int(dist["amount"])
            all_dist_rewards.append(
                distribute_rewards_from_total_snapshot(
                    amount, snapshot, token,
                    block=self.end, custom_rewards=self.CUSTOM_BEHAVIOUR,
                )
            )
        return combine_rewards(all_dist_rewards, self.cycle)
