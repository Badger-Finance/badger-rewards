import pytest
import json
from eth_account import Account

from badger_api.requests import fetch_all_claimable_balances
from rewards.tree_utils import calc_claimable_balances, user_claimable_balances
from rewards.classes.TreeManager import TreeManager
from tests.utils import (
    test_address,
    test_key,
    mock_tree,
    mock_claimable_bals,
    mock_claimed_for,
)
from helpers.constants import BOOST_CHAINS
from unittest import TestCase


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


def test_user_claimable_balances(
    tree_manager: TreeManager, tokens_to_check, expected_user_claimable
):
    claimable_bals = user_claimable_balances(
        test_address, mock_tree["claims"][test_address], tree_manager, tokens_to_check
    )
    TestCase().assertDictEqual(expected_user_claimable, claimable_bals)


def test_calc_claimable_balances(
    tree_manager: TreeManager, tree, tokens_to_check, expected_claimable_bals
):
    all_claimable_bals = calc_claimable_balances(tree_manager, tokens_to_check, tree)
    print(all_claimable_bals)
    print(expected_claimable_bals)
    TestCase().assertDictEqual(expected_claimable_bals, all_claimable_bals)


@pytest.mark.parametrize(
    "chain",
    BOOST_CHAINS,
)
def test_fetch_all_claimable_balances(chain):
    result = fetch_all_claimable_balances(chain)
    assert len(result) > 0
