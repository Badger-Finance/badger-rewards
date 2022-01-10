import logging
from copy import deepcopy
from decimal import Decimal
from math import isclose
from unittest import TestCase

import pytest
from web3 import Web3
from helpers.constants import BADGER, DECIMAL_MAPPING, SETTS
from helpers.enums import BalanceType, Network
from rewards.classes.Schedule import Schedule
from tests.test_subgraph.test_data import BADGER_DISTRIBUTIONS_TEST_DATA
from tests.utils import (
    mock_balances,
    mock_boosts,
    mock_boosts_split,
    mock_tree,
    set_env_vars,
    test_account,
    test_cycle,
    test_end,
    test_start,
)

set_env_vars()

from rewards.classes.RewardsManager import RewardsManager
from rewards.classes.Snapshot import Snapshot
from rewards.utils.rewards_utils import combine_rewards, process_cumulative_rewards
from tests.test_utils.cycle_utils import mock_badger_tree, mock_tree_manager

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
def boosts_split():
    return mock_boosts_split


@pytest.fixture
def balances():
    return mock_balances


def mock_get_sett_multipliers():
    return mock_boosts["multiplierData"]


def mock_get_sett_multipliers_split():
    return mock_boosts_split["multiplierData"]


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


@pytest.fixture
def rewards_manager_split(cycle, start, end, boosts_split, request) -> RewardsManager:
    rewards_manager_split = RewardsManager(
        request.param, cycle, start, end, boosts_split["userData"]
    )
    rewards_manager_split.get_sett_multipliers = mock_get_sett_multipliers_split
    rewards_manager_split.fetch_sett_snapshot = mock_fetch_snapshot
    rewards_manager_split.start = 13609200
    rewards_manager_split.end = 13609300

    return rewards_manager_split


@pytest.fixture
def tree_manager():
    tree_manager = mock_tree_manager(Network.Ethereum, test_account, mock_badger_tree)
    return tree_manager


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
                assert isclose(mult, boosts["userData"][user]["multipliers"][sett], abs_tol=1e-6)


@pytest.mark.parametrize(
    "rewards_manager_split",
    [
        Network.Ethereum,
    ],
    indirect=True,
)
def test_splits(
    rewards_manager_split, schedule, tree_manager, boosts_split, monkeypatch,
    mocker,
):
    rates = [Decimal(0), Decimal(0.5), Decimal(1)]
    user_data = {}
    discord = mocker.patch("rewards.classes.RewardsManager.send_code_block_to_discord")
    for rate in rates:
        monkeypatch.setattr(
            "rewards.classes.RewardsManager.get_flat_emission_rate",
            lambda s, c: rate,
        )
        sett = SETTS[Network.Ethereum]["ibbtc_crv"]
        total_badger = 100
        mock_schedule = {BADGER: [schedule(sett, total_badger)]}
        all_schedules = {sett: mock_schedule}
        all_setts = [sett]

        logger.info(f"Generating rewards with {rate*100}% pro rata rewards")
        rewards_list = []
        tree_rewards = rewards_manager_split.calculate_tree_distributions()
        sett_rewards = rewards_manager_split.calculate_all_sett_rewards(
            all_setts, all_schedules
        )
        rewards_list.append(tree_rewards)
        rewards_list.append(sett_rewards)

        new_rewards = combine_rewards(rewards_list, rewards_manager_split.cycle)
        cumulative_rewards = process_cumulative_rewards(mock_tree, new_rewards)
        merkle_tree = tree_manager.convert_to_merkle_tree(
            cumulative_rewards, rewards_manager_split.start, rewards_manager_split.end
        )

        for user in merkle_tree["claims"]:
            amount = merkle_tree["claims"][user]["cumulativeAmounts"]
            if user not in user_data:
                user_data[user] = {}
            user_data[user]["boost"] = boosts_split["userData"][user]["boost"]
            if "rewards" not in user_data[user]:
                user_data[user]["rewards"] = []
            user_data[user]["rewards"].append(int(amount[0]) /
                                              DECIMAL_MAPPING[str(rewards_manager_split.chain)])
    assert discord.called
    assert discord.call_count == len(rates)
    assert user_data["0xaffb3b889E48745Ce16E90433A61f4bCb95692Fd"]["rewards"] == [
        0.03332222592469277,
        16.683327779629014,
        33.333333333333336,
    ]
    assert user_data["0xbC641f6C6957096857358Cc70df3623715A2ae45"]["rewards"] == [
        33.32222592469177,
        33.327779629012554,
        33.333333333333336,
    ]
    assert user_data["0xA300a5816A53bb7e256f98bf31Cb1FE9a4bbcAf0"]["rewards"] == [
        66.64445184938354,
        49.988892591358436,
        33.333333333333336,
    ]


def test_calculate_tree_distributions__totals(mocker, boosts_split):
    data = {
        'badgerTreeDistributions': deepcopy(
            BADGER_DISTRIBUTIONS_TEST_DATA['badgerTreeDistributions'][:2]
        )
    }
    first_user = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"
    # second_user = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f57"
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            data,
            {'badgerTreeDistributions': []}
        ],
    )
    rewards_manager = RewardsManager(
        Network.Ethereum, 123, 12997653, 13331083, boosts_split["userData"]
    )
    with mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_sett_balances",
        return_value={
            '0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 1000000000000,
            '0x0000000000007F150Bd6f54c40A34d7C3d5e9f57': 4000000000000,
        }
    ):
        tree_rewards = rewards_manager.calculate_tree_distributions()
    assert (
        tree_rewards.claims[first_user]
        [Web3.toChecksumAddress('0x2B5455aac8d64C14786c3a29858E43b5945819C0')]
        == pytest.approx(Decimal(1198684123822457380799 * 0.2))
    )
