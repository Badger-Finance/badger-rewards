import logging
from copy import deepcopy
from decimal import Decimal
from math import isclose
from unittest import TestCase
from unittest.mock import MagicMock
from moto.core import patch_resource
from rewards.aws.helpers import dynamodb
import pytest
from web3 import Web3
from config.constants import addresses
from config.constants.addresses import BADGER, TECH_OPS
from config.constants.addresses import BVECVX_CVX_LP
from config.constants.addresses import ETH_BADGER_TREE
from config.constants.addresses import IBBTC_PEAK
from config.constants.chain_mappings import DECIMAL_MAPPING, SETTS
from helpers.enums import BalanceType, Network
from rewards.classes.RewardsManager import InvalidRewardsTotalException
from rewards.classes.Schedule import Schedule
from tests.test_subgraph.test_data import BADGER_DISTRIBUTIONS_TEST_DATA
from tests.utils import (
    mock_get_claimable_data,
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
from tests.test_utils.cycle_utils import mock_tree_manager

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


def mock_fetch_snapshot(start_block, end_block, sett):
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
def mock_fns(mocker):
    mocker.patch(
        "helpers.discord.send_message_to_discord", mock_send_message_to_discord
    )
    mocker.patch(
        "rewards.snapshot.claims_snapshot.get_claimable_data", mock_get_claimable_data
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
    rewards_manager_split.fetch_sett_snapshot = mock_fetch_snapshot
    rewards_manager_split.get_sett_multipliers = mock_get_sett_multipliers_split
    rewards_manager_split.start = 13609200
    rewards_manager_split.end = 13609300

    return rewards_manager_split


@pytest.fixture
def tree_manager():
    tree_manager = mock_tree_manager(Network.Ethereum, test_account)
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
def schedule(start_time, end_time) -> callable:
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


FIRST_USER = "0xaffb3b889E48745Ce16E90433A61f4bCb95692Fd"
SECOND_USER = "0xbC641f6C6957096857358Cc70df3623715A2ae45"
THIRD_USER = "0xA300a5816A53bb7e256f98bf31Cb1FE9a4bbcAf0"


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
                assert isclose(
                    mult, boosts["userData"][user]["multipliers"][sett], abs_tol=1e-6
                )


@pytest.mark.parametrize(
    "rewards_manager_split",
    [
        Network.Ethereum,
    ],
    indirect=True,
)
def test_splits(
    rewards_manager_split,
    schedule,
    tree_manager,
    boosts_split,
    mocker,
    fetch_token_mock,
):
    rates = [Decimal(0), Decimal(0.5), Decimal(1)]
    user_data = {}
    discord = mocker.patch("rewards.classes.RewardsManager.send_code_block_to_discord")
    for rate in rates:
        mocker.patch(
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
        sett_rewards, __ = rewards_manager_split.calculate_all_sett_rewards(
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
            user_data[user]["rewards"].append(
                int(amount[0]) / DECIMAL_MAPPING[str(rewards_manager_split.chain)]
            )
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


def test_calculate_sett_rewards__check_analytics(
        schedule, mocker, boosts_split, mock_discord, fetch_token_mock,
):
    mocker.patch("rewards.classes.RewardsManager.send_code_block_to_discord")
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_sett_balances",
        return_value={
            FIRST_USER: 1000,
            SECOND_USER: 1000,
            THIRD_USER: 1000,
        }
    )
    sett = SETTS[Network.Ethereum]["ibbtc_crv"]
    total_badger = 100
    badger_schedule = schedule(
        sett, total_badger
    )
    print(badger_schedule)
    print(badger_schedule.startTime)
    print(badger_schedule.endTime)

    all_schedules = {sett: {BADGER: [badger_schedule]}}

    rewards_manager = RewardsManager(
        Network.Ethereum, 123, 13609200, 13609300, boosts_split["userData"]
    )
    rewards_manager.web3 = MagicMock(
        eth=MagicMock(
            get_block=MagicMock(
                side_effect=[{"timestamp": 1636827265}, {"timestamp": 1636828771}]
            )
        )
    )

    __, analytics = rewards_manager.calculate_all_sett_rewards(
        [sett], all_schedules,
    )
    print(analytics)
    for sett, data in analytics.items():
        assert data['sett_name'] is not None
        assert data['boosted_rewards'][BADGER] is not None
        assert data['flat_rewards'] is not None


def test_calculate_sett_rewards__equal_balances_for_period(
        schedule, mocker, boosts_split, mock_discord, fetch_token_mock,
):
    mocker.patch("rewards.classes.RewardsManager.send_code_block_to_discord")
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_sett_balances",
        return_value={
            FIRST_USER: 1000,
            SECOND_USER: 1000,
            THIRD_USER: 1000,
        }
    )
    sett = SETTS[Network.Ethereum]["ibbtc_crv"]
    total_badger = 100
    all_schedules = {sett: {BADGER: [schedule(sett, total_badger)]}}

    rewards_manager = RewardsManager(
        Network.Ethereum, 123, 13609200, 13609300, boosts_split["userData"]
    )

    rewards, __ = rewards_manager.calculate_all_sett_rewards(
        [sett], all_schedules,
    )
    # First user has boost = 1, so they get smallest amount of rewards because of unboosted balance
    assert rewards.claims[FIRST_USER][BADGER] / Decimal(1e18) == pytest.approx(
        Decimal(0.033322225924691)
    )
    # Second user has boost = 1000, so they get bigger portion of rewards
    assert rewards.claims[SECOND_USER][BADGER] / Decimal(1e18) == pytest.approx(
        Decimal(33.32222592469176)
    )
    # Third user has boost = 2000
    assert rewards.claims[THIRD_USER][BADGER] / Decimal(1e18) == pytest.approx(
        Decimal(66.64445184938353)
    )
    # Make sure all distributed rewards equal to total value distributed in schedule
    assert (
        rewards.claims[FIRST_USER][BADGER]
        + rewards.claims[SECOND_USER][BADGER]
        + rewards.claims[THIRD_USER][BADGER]) / Decimal(1e18) == total_badger


@pytest.mark.parametrize(
    "addr",
    [
        BVECVX_CVX_LP,
        IBBTC_PEAK,
        ETH_BADGER_TREE,
        TECH_OPS
    ]
)
def test_calculate_sett_rewards__call_custom_handler(
        schedule, mocker, boosts_split, mock_discord, addr, setup_dynamodb,
        fetch_token_mock, mock_get_token_weight
):
    patch_resource(dynamodb)

    mocker.patch("rewards.classes.RewardsManager.send_code_block_to_discord")
    mocker.patch("rewards.classes.RewardsManager.check_token_totals_in_range")
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_sett_balances",
        return_value={addr: 1000}
    )

    mock_handler = MagicMock()
    RewardsManager.CUSTOM_BEHAVIOUR = {
        addresses.ETH_BADGER_TREE: mock_handler,
        addresses.IBBTC_PEAK: mock_handler,
        addresses.BVECVX_CVX_LP: mock_handler,
        addresses.TECH_OPS: mock_handler,
    }
    sett = SETTS[Network.Ethereum]["ibbtc_crv"]
    all_schedules = {sett: {BADGER: [schedule(sett, 100)]}}

    rewards_manager = RewardsManager(
        Network.Ethereum, 123, 13609200, 13609300, boosts_split["userData"]
    )
    rewards_manager.web3 = MagicMock(
        eth=MagicMock(
            get_block=MagicMock(
                side_effect=[{"timestamp": 100}, {"timestamp": 100000000}]
            )
        )
    )

    rewards_manager.calculate_all_sett_rewards(
        [sett], all_schedules,
    )
    print(RewardsManager.CUSTOM_BEHAVIOUR)
    assert mock_handler.called


def test_calculate_sett_rewards__balances_vary_for_period(
        schedule, mocker, boosts_split, mock_discord, fetch_token_mock,
):
    mocker.patch("rewards.classes.RewardsManager.send_code_block_to_discord")

    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_sett_balances",
        side_effect=[
            {
                FIRST_USER: 1000,
                SECOND_USER: 1000,
                THIRD_USER: 1000,
            },
            {
                FIRST_USER: 1000,
                SECOND_USER: 10000,
                THIRD_USER: 100,
            },
            {
                FIRST_USER: 1000,
                SECOND_USER: 100000,
                THIRD_USER: 10,
            },
        ]
    )
    sett = SETTS[Network.Ethereum]["ibbtc_crv"]
    total_badger = 100
    all_schedules = {sett: {BADGER: [schedule(sett, total_badger)]}}

    rewards_manager = RewardsManager(
        Network.Ethereum, 123, 13609200, 13609300, boosts_split["userData"]
    )

    rewards, __ = rewards_manager.calculate_all_sett_rewards(
        [sett], all_schedules,
    )
    assert rewards.claims[FIRST_USER][BADGER] / Decimal(1e18) == pytest.approx(
        Decimal(0.00264963832)
    )
    # As second user increased his balance he got more rewards than others
    assert rewards.claims[SECOND_USER][BADGER] / Decimal(1e18) == pytest.approx(
        Decimal(98.036618001642)
    )
    # Third user withdrew funds resulting in much smaller reward
    assert rewards.claims[THIRD_USER][BADGER] / Decimal(1e18) == pytest.approx(
        Decimal(1.960732360032)
    )
    assert (
        rewards.claims[FIRST_USER][BADGER]
        + rewards.claims[SECOND_USER][BADGER]
        + rewards.claims[THIRD_USER][BADGER]) / Decimal(1e18) == total_badger


def test_calculate_tree_distributions__totals(mocker, boosts_split, fetch_token_mock):
    first_user = Web3.toChecksumAddress("0x0000000000007F150Bd6f54c40A34d7C3d5e9f56")
    second_user = Web3.toChecksumAddress("0x0000000000007F150Bd6f54c40A34d7C3d5e9f57")
    token = Web3.toChecksumAddress('0x2B5455aac8d64C14786c3a29858E43b5945819C0')
    another_token = Web3.toChecksumAddress('0x53c8e199eb2cb7c01543c137078a038937a68e40')
    first_amount_distributed = (
        int(BADGER_DISTRIBUTIONS_TEST_DATA['badgerTreeDistributions'][:2][0]['amount'])
    )
    second_amount_distributed = (
        int(BADGER_DISTRIBUTIONS_TEST_DATA['badgerTreeDistributions'][:2][1]['amount'])
    )
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            {
                'badgerTreeDistributions': deepcopy(
                    BADGER_DISTRIBUTIONS_TEST_DATA['badgerTreeDistributions'][:2]
                )
            },
            {'badgerTreeDistributions': []}
        ],
    )
    rewards_manager = RewardsManager(
        Network.Ethereum, 123, 12997653, 13331083, boosts_split["userData"]
    )
    rewards_manager.web3 = MagicMock(
        eth=MagicMock(
            get_block=MagicMock(
                side_effect=[{"timestamp": 100}, {"timestamp": 100000000}]
            )
        )
    )

    with mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_sett_balances",
        return_value={
            first_user: 1000000000000,
            second_user: 4000000000000,
        }
    ):
        tree_rewards = rewards_manager.calculate_tree_distributions()
    # First user gets 20% of total rewards, second one gets 80%
    assert (
        tree_rewards.claims[first_user][token] ==
        pytest.approx(Decimal(first_amount_distributed * 0.2))
    )
    assert (
        tree_rewards.claims[second_user][token] ==
        pytest.approx(Decimal(first_amount_distributed * 0.8))
    )

    assert (
        tree_rewards.claims[first_user][another_token] ==
        pytest.approx(Decimal(second_amount_distributed * 0.2))
    )
    assert (
        tree_rewards.claims[second_user][another_token] ==
        pytest.approx(Decimal(second_amount_distributed * 0.8))
    )


def test_report_invalid_totals(mocker, boosts_split):
    block = mocker.patch("rewards.classes.RewardsManager.send_code_block_to_discord")
    plain_text = mocker.patch("rewards.classes.RewardsManager.send_plain_text_to_discord")
    rewards_manager = RewardsManager(
        Network.Ethereum, 123, 12997653, 13331083, boosts_split["userData"]
    )
    with pytest.raises(InvalidRewardsTotalException):
        rewards_manager.report_invalid_totals([])

    assert block.call_count == 1
    assert plain_text.call_count == 1
