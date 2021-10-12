import os
import pytest
import json
from tests.utils import mock_boosts, test_cycle, test_start, test_end
from unittest import TestCase

os.environ["KUBE"] = "False"
os.environ["TEST"] = "True"

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
    ["eth"],
    indirect=True,
)
def test_get_user_multipliers(rewards_manager: RewardsManager, boosts):
    user_multipliers = rewards_manager.get_user_multipliers()
    for user, data in user_multipliers.items():
        for sett, mult in data.items():
            if sett in boosts["userData"][user]["multipliers"]:
                assert mult == boosts["userData"][user]["multipliers"][sett]
