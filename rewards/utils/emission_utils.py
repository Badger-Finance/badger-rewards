import time
from decimal import Decimal
from functools import lru_cache
from typing import Dict, List

from rich.console import Console
from web3 import Web3
from web3.contract import ContractFunctions

from config.constants.addresses import ACROSS_BRIDGE
from config.constants.chain_mappings import EMISSIONS_CONTRACTS
from config.constants.emissions import DISABLED_VAULTS, NATIVE
from helpers.discord import get_discord_url, send_message_to_discord
from helpers.enums import Abi, BotType, Network
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
    schedules = parse_nft_weight_schedules(nft_control.getNftWeightSchedules().call())
    weights = {}
    for weight_schedule in schedules:
        key = f"{weight_schedule.addr}-{weight_schedule.nft_id}"
        if key not in weights:
            weights[key] = weight_schedule
        else:
            weights[key] = (
                weight_schedule
                if weight_schedule.timestamp > weights[key].timestamp
                else weights[key]
            )
    return weights


def get_nft_weight(chain: str, nft_address: str, nft_id: int) -> Decimal:
    weights = get_nft_weights(chain)
    key = f"{nft_address}-{nft_id}"
    if key in weights:
        return Decimal(weights[key].weight / 1e18)
    else:
        send_message_to_discord(
            "**ERROR**" f"Cannot find weights for {key}",
            [],
            "Boost Bot",
            url=get_discord_url(chain, bot_type=BotType.Boost),
        )
        raise Exception


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


def get_schedules_by_token(schedules: List[Schedule]) -> Dict[str, List[Schedule]]:
    schedules_by_token = {}
    for schedule in schedules:
        if schedule.token not in schedules_by_token:
            schedules_by_token[schedule.token] = []
        schedules_by_token[schedule.token].append(schedule)
    return schedules_by_token


def parse_schedule(schedule) -> Schedule:
    return Schedule(
        Web3.toChecksumAddress(schedule[0]),  # sett
        Web3.toChecksumAddress(schedule[1]),  # token
        schedule[2],  # tokensLocked
        schedule[3],  # startTime
        schedule[4],  # endTime
        schedule[5],  # duration
    )


def parse_nft_weight_schedule(weight_schedule: List) -> NFTWeightSchedule:
    return NFTWeightSchedule(
        weight_schedule[0],  # nft addr
        weight_schedule[1],  # nft id
        weight_schedule[2],  # nft weight
        weight_schedule[3],  # timestamp
    )


def parse_nft_weight_schedules(weight_schedules: List) -> List[NFTWeightSchedule]:
    return [parse_nft_weight_schedule(ws) for ws in weight_schedules]


def get_across_lp_multiplier() -> float:
    bridge = make_contract(ACROSS_BRIDGE, abi_name=Abi.BridgePoolProd, chain=Network.Ethereum)

    liquid_reserves = bridge.liquidReserves().call()
    utilized_reserves = max(bridge.utilizedReserves().call(), 0)
    undistributed_lp_fees = bridge.undistributedLpFees().call()
    total_supply = bridge.totalSupply().call()
    return (liquid_reserves + utilized_reserves - undistributed_lp_fees) / total_supply
