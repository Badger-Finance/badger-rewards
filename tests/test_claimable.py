import json
import os

import pytest
from eth_account import Account
from moto.core import patch_resource

from badger_api.claimable import get_latest_claimable_snapshot
from rewards.aws.helpers import dynamodb
from tests.utils import (
    chains,
    mock_claimable_bals,
    mock_claimed_for,
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
    get_latest_claimable_snapshot(chain)
