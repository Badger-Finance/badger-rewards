import json

import pytest
from eth_account import Account
from moto.core import patch_resource

from rewards.aws.helpers import dynamodb
from tests.utils import (
    chains,
    mock_tree,
    set_env_vars,
    test_key,
)

set_env_vars()

from rewards.classes.TreeManager import TreeManager
from rewards.utils.tree_utils import (
    calc_next_cycle_range,
    get_last_proposed_cycle,
)


def mock_download_tree(file_name: str, chain: str):
    return json.dumps(mock_tree)


def mock_validate_tree(merkle, tree):
    return True


@pytest.fixture(autouse=True)
def mock_fns(monkeypatch):
    monkeypatch.setattr("rewards.classes.TreeManager.download_tree", mock_download_tree)


@pytest.fixture
def cycle_key() -> str:
    return test_key


@pytest.fixture
def tree_manager(cycle_key, request) -> TreeManager:
    tree_manager = TreeManager(request.param, Account.from_key(cycle_key))
    tree_manager.validate_tree = mock_validate_tree
    tree_manager.last_publish_end_block = lambda: 0
    return tree_manager


@pytest.mark.parametrize(
    "tree_manager",
    chains,
    indirect=True,
)
def test_get_last_proposed_cycle(tree_manager):
    tree_manager.has_pending_root = lambda: True
    rewards = tree_manager.fetch_current_tree()
    claim_end = tree_manager.last_propose_end_block()
    claim_start = tree_manager.last_propose_start_block()
    assert get_last_proposed_cycle(tree_manager.chain, tree_manager) == (
        rewards,
        claim_start,
        claim_end,
    )
    tree_manager.has_pending_root = lambda: False
    assert get_last_proposed_cycle(tree_manager.chain, tree_manager) == ({}, 0, 0)


@pytest.mark.parametrize(
    "tree_manager",
    chains,
    indirect=True,
)
def test_calc_next_cycle_range(tree_manager, setup_dynamodb):
    patch_resource(dynamodb)

    result = calc_next_cycle_range(tree_manager.chain, tree_manager)
    assert result[0] == mock_tree
