import json
import logging
from unittest import TestCase

import pytest
from brownie import web3

from helpers.constants import BADGER, SETTS
from helpers.enums import BalanceType, Network
from rewards.classes.Schedule import Schedule
from tests.utils import (mock_balances, mock_boosts, mock_tree, set_env_vars,
                         test_cycle, test_end, test_start)

set_env_vars()

from rewards.classes.RewardsManager import RewardsManager
from rewards.classes.Snapshot import Snapshot
from rewards.classes.TreeManager import TreeManager
from rewards.utils.rewards_utils import (combine_rewards,
                                         process_cumulative_rewards)

logger = logging.getLogger("test-rewards-manager")


@pytest.fixture
def cycle() -> int:
    return test_cycle


@pytest.fixture
def start() -> int:
    return test_start


@pytest.fixture
def end() -> bool:
    return test_end


@pytest.fixture
def boosts():
    return mock_boosts


@pytest.fixture
def balances():
    return mock_balances


def mock_get_sett_multipliers():
    return mock_boosts["multiplierData"]


def mock_tree_manager(chain, cycle_account, badger_tree):
    with open(f"abis/eth/BadgerTreeV2.json") as fp:
        abi = json.load(fp)
    tree_manager = TreeManager(chain, cycle_account)
    tree_manager.fetch_current_tree = mock_fetch_current_tree
    tree_manager.w3 = web3
    tree_manager.badger_tree = web3.eth.contract(
        address=EMISSIONS_CONTRACTS[chain]["BadgerTree"], abi=abi
    ).functions
    return tree_manager


def mock_fetch_snapshot(block, sett):
    return Snapshot(
        sett,
        mock_balances,
        ratio=1,
        type=BalanceType.NonNative,
    )


def mock_send_message_to_discord(
    title: str, description: str, fields: list, username: str, url: str = ""
):
    return True


@pytest.fixture(autouse=True)
def mock_fns(monkeypatch):
    monkeypatch.setattr(
        "helpers.discord.send_message_to_discord", mock_send_message_to_discord
    )


@pytest.fixture
def rewards_manager(cycle, start, end, boosts, request) -> RewardsManager:
    rewards_manager = RewardsManager(
        request.param, cycle, start, end, boosts["userData"]
    )
    rewards_manager.get_sett_multipliers = mock_get_sett_multipliers

    return rewards_manager


@pytest.fixture()
def emission_rate(request) -> float:
    return request.param


@pytest.fixture()
def sett(request) -> str:
    return request.param


@pytest.fixture
def start_time() -> int:
    return 1636827266


@pytest.fixture
def end_time() -> int:
    return 1636828770


@pytest.fixture
def schedule(start_time, end_time) -> int:
    def _method(sett, total_amount):
        return Schedule(
            sett,
            BADGER,
            total_amount * 1e18,
            startTime=start_time,
            endTime=end_time,
            duration=10,
        )

    return _method


@pytest.mark.parametrize(
    "rewards_manager",
    [Network.Ethereum],
    indirect=True,
)
def test_boost_sett(rewards_manager: RewardsManager, balances):
    sett = "0xd04c48A53c111300aD41190D63681ed3dAd998eC"
    boosted_bals = {
        "0xaffb3b889E48745Ce16E90433A61f4bCb95692Fd": 200000,
        "0xbC641f6C6957096857358Cc70df3623715A2ae45": 50000,
        "0xA300a5816A53bb7e256f98bf31Cb1FE9a4bbcAf0": 1600000,
    }
    boosted = rewards_manager.boost_sett(
        sett, Snapshot(sett, balances, ratio=1, type=BalanceType.NonNative)
    )
    TestCase().assertDictEqual(d1=boosted.balances, d2=boosted_bals)


@pytest.mark.parametrize(
    "rewards_manager",
    [Network.Ethereum],
    indirect=True,
)
def test_get_user_multipliers(rewards_manager: RewardsManager, boosts):
    user_multipliers = rewards_manager.get_user_multipliers()
    for user, data in user_multipliers.items():
        for sett, mult in data.items():
            if sett in boosts["userData"][user]["multipliers"]:
                assert mult == boosts["userData"][user]["multipliers"][sett]


@pytest.mark.parametrize(
    "rewards_manager, emission_rate, sett",
    [
        (Network.Ethereum, 0.49, SETTS[Network.Ethereum]["ibbtc_crv"]),
        (Network.Ethereum, 1, SETTS[Network.Ethereum]["bvecvx"]),
        (Network.Ethereum, 0, SETTS[Network.Ethereum]["sbtc_crv"]),
    ],
    indirect=True,
)
def test_calculate_sett_rewards(
    rewards_manager: RewardsManager, emission_rate, sett, monkeypatch, schedule
):
    rewards_manager.fetch_sett_snapshot = mock_fetch_snapshot
    monkeypatch.setattr(
        "rewards.utils.emission_utils.get_flat_emission_rate",
        lambda s, c: emission_rate,
    )
    rewards_manager.start = 13609200
    rewards_manager.end = 13609300
    badger_decimals_conversion = 1e18
    total_badger = 100
    mock_schedule = {BADGER: [schedule(sett, total_badger)]}

    rewards, flat, boosted = rewards_manager.calculate_sett_rewards(
        sett, schedules_by_token=mock_schedule
    )
    test_case = TestCase()
    total_flat = sum(flat.totals.values()) / badger_decimals_conversion
    logger.info(total_flat)
    total_boosted = sum(boosted.totals.values()) / badger_decimals_conversion
    logger.info(total_boosted)
    total_rewards = sum(rewards.totals.values()) / badger_decimals_conversion
    logger.info(total_rewards)
    test_case.assertAlmostEqual(total_boosted + total_flat, total_rewards)
    test_case.assertAlmostEqual(total_boosted, (1 - emission_rate) * total_badger)
    test_case.assertAlmostEqual(total_flat, emission_rate * total_badger)


@pytest.mark.parametrize(
    "emission_rate",
    [
        0,  # flat
        0.49,  # middle
        1,  # full boost
    ],
    indirect=True,
)
def test_splits(schedule, rewards_manager, emission_rate, monkeypatch):
    monkeypatch.setattr(
        "rewards.utils.emission_utils.get_flat_emission_rate",
        lambda s, c: emission_rate,
    )

    ###
    total_badger = 100
    schedule = {BADGER: [schedule(BIBBTC_CURVE_LP, total_badger)]}
    all_schedules, setts = schedule, list(BIBBTC_CURVE_LP)

    logger.info(f"Generating rewards for {len(setts)} setts on {Network.Ethereum}")

    rewards_list = []
    boosts = mock_boosts

    logger.info("Calculating Tree Rewards...")
    tree_rewards = rewards_manager.calculate_tree_distributions()
    rewards_list.append(tree_rewards)

    logger.info("Calculating Sett Rewards...")
    sett_rewards = rewards_manager.calculate_all_sett_rewards(setts, all_schedules)
    rewards_list.append(sett_rewards)

    new_rewards = combine_rewards(rewards_list, rewards_manager.cycle)

    start_block, end_block = 13609200, 13609300

    logger.info("Combining cumulative rewards... \n")
    cumulative_rewards = process_cumulative_rewards(mock_tree, new_rewards)

    logger.info("Converting to merkle tree... \n")
    merkle_tree = tree_manager.convert_to_merkle_tree(
        cumulative_rewards, start_block, end_block
    )
    logger.info(merkle_tree)


# def test_splits_sett_rewards(
#     rewards_manager: RewardsManager, emission_rate, sett, monkeypatch, schedule
# ):
#     rewards_manager.fetch_sett_snapshot = mock_fetch_snapshot
#     monkeypatch.setattr(
#         "rewards.utils.emission_utils.get_flat_emission_rate",
#         lambda s, c: emission_rate,
#     )
#     rewards_manager.start = 13609200
#     rewards_manager.end = 13609300
#     badger_decimals_conversion = 1e18
#     total_badger = 100
#     mock_schedule = {BADGER: [schedule(sett, total_badger)]}

#     rewards, flat, boosted = rewards_manager.calculate_sett_rewards(
#         sett, schedules_by_token=mock_schedule
#     )
#     test_case = TestCase()
#     total_flat = sum(flat.totals.values()) / badger_decimals_conversion
#     print(total_flat)
#     total_boosted = sum(boosted.totals.values()) / badger_decimals_conversion
#     print(total_boosted)
#     total_rewards = sum(rewards.totals.values()) / badger_decimals_conversion
#     print(total_rewards)
#     test_case.assertAlmostEqual(total_boosted + total_flat, total_rewards)
#     test_case.assertAlmostEqual(total_boosted, (1 - emission_rate) * total_badger)
#     test_case.assertAlmostEqual(total_flat, emission_rate * total_badger)
