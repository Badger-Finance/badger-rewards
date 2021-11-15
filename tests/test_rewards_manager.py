from unittest import TestCase

import pytest

from helpers.constants import BADGER, SETTS
from helpers.enums import BalanceType, Network
from rewards.classes.Schedule import Schedule
from rewards.classes.Snapshot import Snapshot
from tests.utils import (mock_balances, mock_boosts, set_env_vars, test_cycle,
                         test_end, test_start)

set_env_vars()

from rewards.classes.RewardsManager import RewardsManager


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
    def _method(sett, total_amouht):
        return Schedule(
            sett,
            BADGER,
            total_amouht * 1e18,
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
    total_boosted = sum(boosted.totals.values()) / badger_decimals_conversion
    total_rewards = sum(rewards.totals.values()) / badger_decimals_conversion
    test_case.assertAlmostEqual(total_boosted + total_flat, total_rewards)
    test_case.assertAlmostEqual(total_boosted, (1 - emission_rate) * total_badger)
    test_case.assertAlmostEqual(total_flat, emission_rate * total_badger)
