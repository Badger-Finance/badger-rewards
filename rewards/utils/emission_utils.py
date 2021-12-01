import time
from decimal import Decimal
from functools import lru_cache
from typing import Dict, List

from rich.console import Console
from web3 import Web3
from web3.contract import ContractFunctions

from helpers.constants import DISABLED_VAULTS, EMISSIONS_CONTRACTS, NATIVE
from helpers.enums import Abi, Network
from helpers.web3_utils import make_contract
from rewards.classes.NftWeightSchedule import NFTWeightSchedule
from rewards.classes.Schedule import Schedule
from subgraph.queries.setts import list_setts

console = Console()


@lru_cache
def get_emission_control(chain: Network) -> ContractFunctions:
    return make_contract(
        EMISSIONS_CONTRACTS[chain]["EmissionControl"], Abi.EmissionControl, chain
    )


def get_token_weight(token: str, chain: str) -> float:
    token_weight = get_emission_control(chain).tokenWeight(token).call() / 1e4
    return 1 if token_weight == 0 else token_weight


def get_flat_emission_rate(sett: str, chain: str) -> Decimal:
    return Decimal(get_emission_control(chain).proRataEmissionRate(sett).call() / 1e4)


@lru_cache
def get_nft_control(chain: Network) -> ContractFunctions:
    return make_contract(
        EMISSIONS_CONTRACTS[chain]["NFTControl"], Abi.NFTControl, chain
    )


@lru_cache
def get_nft_weights(chain: Network):
    nft_control = get_nft_control(chain)
    schedules = parse_nft_weight_schedules(nft_control.getNftWeightSchedules.call())
    weights = {}
    for weight_schedule in schedules:
        key = f"{weight_schedule.addr}-{weight_schedule.nft_id}"
        if key not in weights:
            weights[key] = weight_schedule
        else:
            curr_schedule = weights[key]
            if weight_schedule.timestamp > curr_schedule.timestamp:
                weights[key] = weight_schedule
    return weights


def get_nft_weight(chain: str, nft_address: str, nft_id: int) -> Decimal:
    weights = get_nft_weights(chain)
    return Decimal(weights[f"{nft_address}-{nft_id}"].weight / 1e18)


def fetch_unboosted_vaults(chain) -> List[str]:
    all_setts = fetch_setts(chain)
    logger = make_contract(
        EMISSIONS_CONTRACTS[chain]["RewardsLogger"], Abi.RewardsLogger, chain
    )
    unboosted_vaults = []
    now = time.time()
    for sett in all_setts:
        schedules = logger.getAllUnlockSchedulesFor(sett).call()
        has_active_schedule = False
        for schedule in schedules:
            schedule = parse_schedule(schedule)
            if schedule.startTime < now < schedule.endTime:
                has_active_schedule = True
        if not has_active_schedule and sett not in NATIVE:
            unboosted_vaults.append(sett)
    return unboosted_vaults


def fetch_setts(chain: str) -> List[str]:
    """
    Fetch setts that are eligible for rewards
    :param chain:
    """
    setts = list_setts(chain)
    return list(filter(lambda x: x not in DISABLED_VAULTS, setts))


def parse_schedules(schedules) -> Dict[str, List[Schedule]]:
    """
    Parse unlock shcedules
    :param schedules: schedules to parse
    """
    schedules_by_token = {}
    console.log("Fetching schedules...")
    for schedule in schedules:
        schedule = parse_schedule(schedule)
        if schedule.token not in schedules_by_token:
            schedules_by_token[schedule.token] = []
        schedules_by_token[schedule.token].append(schedule)
    return schedules_by_token


def parse_schedule(schedule) -> Schedule:
    return Schedule(
        Web3.toChecksumAddress(schedule[0]),
        Web3.toChecksumAddress(schedule[1]),
        schedule[2],
        schedule[3],
        schedule[4],
        schedule[5],
    )


def parse_nft_weight_schedule(weight_schedule: List) -> NFTWeightSchedule:
    return NFTWeightSchedule(
        weight_schedule[0],
        weight_schedule[1],
        weight_schedule[2],
        weight_schedule[3],
    )


def parse_nft_weight_schedules(weight_schedules: List) -> List[NFTWeightSchedule]:
    return [parse_nft_weight_schedule(ws) for ws in weight_schedules]
