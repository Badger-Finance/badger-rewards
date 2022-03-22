from unittest.mock import MagicMock
import pytest
from brownie import accounts
from config.constants import addresses
from config.singletons import env_config
from helpers.enums import Network
from rewards.calc_rewards import approve_root, fetch_all_schedules
from rewards.classes.TreeManager import TreeManager


@pytest.fixture
def prepare_approve_mocks(mocker):
    mocker.patch("rewards.calc_rewards.download_proposed_boosts",
                 return_value={})
    mocker.patch(
        "rewards.calc_rewards.generate_rewards_in_range",
        return_value={
            'rootHash': "123",
            'multiplierData': {},
            'userMultipliers': {},
            'sett_rewards_analytics': {},
            'fileName': "something",
            'merkleTree': {'merkleRoot': "123"}
        }
    )
    mocker.patch("rewards.calc_rewards.upload_tree")
    mocker.patch("rewards.calc_rewards.add_multipliers")
    mocker.patch("rewards.calc_rewards.upload_boosts")
    mocker.patch("rewards.calc_rewards.env_config.test", False)
    mocker.patch("rewards.calc_rewards.env_config.production", True)
    yield


def test_approve_root__calls_analytics_store(mocker, prepare_approve_mocks):
    """
    Case when approve_root() returns success True, rewards data should be stored
    """
    dynamo_put_reward = mocker.patch(
        "rewards.calc_rewards.put_rewards_data",
    )
    tree_manager = TreeManager(Network.Ethereum, accounts[0])
    tree_manager.matches_pending_hash = lambda _: True
    tree_manager.approve_root = lambda _: ("some_hash", True)
    approve_root(
        Network.Ethereum,
        123, 123, {}, tree_manager
    )
    assert dynamo_put_reward.called


def test_approve_root__unhappy(mocker, prepare_approve_mocks):
    """
    Case when approve_root() returns success False, rewards data should not be stored
    """
    dynamo_put_reward = mocker.patch(
        "rewards.calc_rewards.put_rewards_data",
    )
    tree_manager = TreeManager(Network.Ethereum, accounts[0])
    tree_manager.matches_pending_hash = lambda _: True
    tree_manager.approve_root = lambda _: ("some_hash", False)
    approve_root(
        Network.Ethereum,
        123, 123, {}, tree_manager
    )
    assert not dynamo_put_reward.called


def test_fetch_all_schedules(mocker):
    setts = [
        addresses.BCRV_IBBTC,
    ]

    SCHEDULES = [
        [
            addresses.BCRV_IBBTC,
            addresses.BADGER,
            1e18,
            0,
            100,
            100
        ],
        [
            addresses.BCRV_IBBTC,
            addresses.BADGER,
            1e18,
            150,
            250,
            100
        ]
    ]

    mocker.patch(
        "rewards.calc_rewards.make_contract",
        return_value=MagicMock(
            getAllUnlockSchedulesFor=MagicMock(
                return_value=MagicMock(call=MagicMock(return_value=SCHEDULES)),
            )
        )
    )

    def mock_ts(timestamp):
        return {"timestamp": timestamp}
    env_config.get_web3 = MagicMock(
        return_value=MagicMock(
            eth=MagicMock(
                get_block=MagicMock(
                    side_effect=[mock_ts(i) for i in [101, 200, 175, 225]]
                )
            )
        )
    )
    mocker.patch(
        "rewards.calc_rewards.env_config",
        env_config
    )

    mocker.patch(
        "rewards.calc_rewards.fetch_setts",
        return_value=setts
    )

    all_schedules, setts_with_schedules = fetch_all_schedules(
        Network.Ethereum,
        10,
        20
    )
    assert setts_with_schedules == [addresses.BCRV_IBBTC]
    assert len(all_schedules[addresses.BCRV_IBBTC]) == 1
