import json
from unittest.mock import MagicMock

import pytest
from brownie import accounts
from eth_account import Account
from config.constants import GAS_BUFFER
from helpers.enums import Network
from rewards.utils.tx_utils import create_tx_options
from tests.test_utils.cycle_utils import mock_tree_manager
from tests.utils import mock_tree
from tests.utils import set_env_vars
from tests.utils import test_key

set_env_vars()

from rewards.classes.TreeManager import TreeManager


def mock_download_tree(file_name: str, chain: str):
    return json.dumps(mock_tree)


def mock_validate_tree(merkle, tree):
    return True


@pytest.fixture(autouse=True)
def mock_fns(mocker):
    mocker.patch("rewards.classes.TreeManager.download_tree", mock_download_tree)


@pytest.fixture
def cycle_key() -> str:
    return test_key


def mock_get_tx_options(account):
    return {}


@pytest.fixture
def tree_manager(cycle_key, request) -> TreeManager:
    tree_manager = TreeManager(request.param, Account.from_key(cycle_key))
    tree_manager.validate_tree = mock_validate_tree
    return tree_manager


def test_ftm_tx_details__gas_price(mocker):
    gas_price = 123
    mocker.patch("rewards.classes.TreeManager.env_config.get_web3", return_value=MagicMock())
    mocker.patch("rewards.classes.TreeManager.get_badger_tree", MagicMock())
    mocker.patch("rewards.classes.TreeManager.get_discord_url", MagicMock())
    tree_manager = mock_tree_manager(Network.Fantom, accounts[0])
    tree_manager.w3 = MagicMock(eth=MagicMock(gas_price=gas_price))
    assert (
        create_tx_options(accounts[0], tree_manager.w3, Network.Fantom)['gasPrice']
        == int(gas_price * GAS_BUFFER)
    )
