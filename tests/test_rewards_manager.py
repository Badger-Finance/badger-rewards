import os
import pytest
import json
from rewards.classes.Snapshot import Snapshot
from tests.utils import mock_boosts, test_cycle, test_start, test_end, set_env_vars, mock_balances
from unittest import TestCase
from helpers.enums import Network, BalanceType

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


@pytest.fixture
def rewards_manager(cycle, start, end, boosts, request) -> RewardsManager:
    rewards_manager = RewardsManager(
        request.param, cycle, start, end, boosts["userData"]
    )
    rewards_manager.get_sett_multipliers = mock_get_sett_multipliers
    return rewards_manager

@pytest.mark.parametrize(
    "rewards_manager",
    [Network.Ethereum],
    indirect=True,
)
def test_boost_sett(rewards_manager: RewardsManager, balances):
    sett = "0xd04c48A53c111300aD41190D63681ed3dAd998eC"
    boosted_bals = {
        "0xaffb3b889E48745Ce16E90433A61f4bCb95692Fd": 2000,
        "0xbC641f6C6957096857358Cc70df3623715A2ae45": 50000,
        "0xA300a5816A53bb7e256f98bf31Cb1FE9a4bbcAf0": 3712000
    }
    boosted = rewards_manager.boost_sett(sett, Snapshot(sett, balances, ratio=1, type=BalanceType.NonNative))
    print(boosted)
    print(boosted_bals)
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
