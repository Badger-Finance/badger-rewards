import json

import pytest
from botocore.exceptions import ClientError
from eth_account import Account
from gql.client import Client
from moto.core import patch_resource

from badger_api.claimable import get_latest_claimable_snapshot
from helpers.enums import Network
from rewards.aws.helpers import dynamodb
from tests.utils import (
    chains,
    mock_claimable_bals,
    mock_claimed_for,
    mock_send_message_to_discord_prod,
    mock_tree,
    set_env_vars,
    test_address,
    test_key,
)

set_env_vars()

from unittest import TestCase

from helpers.constants import BOOST_CHAINS
from rewards.classes.TreeManager import TreeManager


def mock_download_tree(file_name: str, chain: str):
    return json.dumps(mock_tree)


def mock_validate_tree(merkle, tree):
    return True


def mock_get_claimed_for(user, tokens_to_check):
    return mock_claimed_for[user]


@pytest.fixture
def expected_user_claimable():
    return mock_claimable_bals[test_address]


@pytest.fixture
def expected_claimable_bals():
    return mock_claimable_bals


@pytest.fixture(autouse=True)
def mock_fns(monkeypatch):
    monkeypatch.setattr("rewards.classes.TreeManager.download_tree", mock_download_tree)


@pytest.fixture
def tree():
    return mock_tree


@pytest.fixture
def tokens_to_check(tree):
    return list(tree["tokenTotals"].keys())


@pytest.fixture
def cycle_key() -> str:
    return test_key


@pytest.fixture
def tree_manager(cycle_key) -> TreeManager:
    tree_manager = TreeManager("eth", Account.from_key(cycle_key))
    tree_manager.validate_tree = mock_validate_tree
    tree_manager.get_claimed_for = mock_get_claimed_for
    return tree_manager


@pytest.mark.parametrize("chain", chains)
def test_get_latest_claimable_snapshot(chain, setup_dynamodb):
    patch_resource(dynamodb)
    cb_snapshot = get_latest_claimable_snapshot(chain)
    assert len(cb_snapshot) > 0
    for cb_data in cb_snapshot:
        assert 'address' in cb_data
        assert 'chain' in cb_data
        assert 'claimableBalances' in cb_data


def raise_client_error(chain, block):
    raise ClientError({}, "")


def test_latest_claimable_snapshot_unhappy(setup_dynamodb, mock_discord, mocker):
    patch_resource(dynamodb)
    mocker.patch("badger_api.claimable.get_claimable_balances", side_effect=raise_client_error)
    with pytest.raises(ClientError):
        cb_snapshot = get_latest_claimable_snapshot(Network.Ethereum)
        # Make sure discord message was sent
        assert mock_discord.called
        # Make sure only one message was sent to discord
        assert mock_discord.call_count == 1
