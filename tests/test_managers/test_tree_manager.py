import json
from unittest.mock import MagicMock

import pytest
from brownie import accounts
from eth_account import Account
import config.constants.addresses as addresses
from config.constants import GAS_BUFFER
from helpers.enums import Network
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


def mock_get_tx_options():
    return {}


@pytest.fixture
def tree_manager(cycle_key, request) -> TreeManager:
    tree_manager = TreeManager(request.param, Account.from_key(cycle_key))
    tree_manager.validate_tree = mock_validate_tree
    return tree_manager


@pytest.mark.parametrize(
    "tree_manager",
    [Network.Ethereum],
    indirect=True,
)
def test_matches_pending_hash(tree_manager):
    pending_hash = tree_manager.badger_tree.pendingMerkleContentHash().call()
    assert tree_manager.matches_pending_hash(pending_hash)

    random_hash = "0xb8ed7da2062b6bdf6f20bcdb4ab35538592216ac70a4bfe986af748603debfd8"
    assert not tree_manager.matches_pending_hash(random_hash)


@pytest.mark.parametrize(
    "tree_manager",
    [Network.Ethereum],
    indirect=True,
)
def test_build_function_and_send(tree_manager, mocker):
    mocker.patch("rewards.classes.TreeManager.build_and_send")
    tree_manager.get_tx_options = mock_get_tx_options
    tree_manager.build_function_and_send(account=None, func=None)


@pytest.mark.parametrize(
    "tree_manager",
    [Network.Ethereum],
    indirect=True,
)
def test_get_claimed_for(tree_manager):
    user = "0xEE9F84Af6a8251Eb5ffDe38c5F056bc72d3b3DD0"
    tokens = [
        addresses.BADGER,
        addresses.BVECVX
    ]
    claimed_for_tokens = tree_manager.get_claimed_for(
        user,
        tokens
    )
    for token in tokens:
        assert claimed_for_tokens[token] > 0


def test_ftm_tx_details__gas_price(mocker):
    gas_price = 123
    mocker.patch("rewards.classes.TreeManager.env_config.get_web3", return_value=MagicMock())
    mocker.patch("rewards.classes.TreeManager.get_badger_tree", MagicMock())
    mocker.patch("rewards.classes.TreeManager.get_discord_url", MagicMock())
    tree_manager = mock_tree_manager(Network.Fantom, accounts[0])
    tree_manager.w3 = MagicMock(eth=MagicMock(gas_price=gas_price))
    assert (
        tree_manager.get_tx_options(accounts[0])['gasPrice']
        == int(gas_price * GAS_BUFFER)
    )
