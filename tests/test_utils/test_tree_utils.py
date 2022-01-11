import json
import os

import pytest
from eth_account import Account

from tests.utils import chains, mock_tree, set_env_vars, test_address, test_key

set_env_vars()

from rewards.classes.TreeManager import TreeManager
from rewards.utils.tree_utils import calc_next_cycle_range, get_last_proposed_cycle


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
    return tree_manager


@pytest.mark.parametrize(
    "tree_manager",
    chains,
    indirect=True,
)
def test_get_last_proposed_cycle(tree_manager):
    if tree_manager.has_pending_root():
        rewards = tree_manager.fetch_current_tree()
        claim_end = tree_manager.last_propose_end_block()
        claim_start = tree_manager.last_propose_start_block()
        assert get_last_proposed_cycle(tree_manager.chain, tree_manager) == (
            rewards,
            claim_start,
            claim_end,
        )
    else:
        assert get_last_proposed_cycle(tree_manager.chain, tree_manager) == ({}, 0, 0)

@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-west-1"


@pytest.mark.parametrize(
    "tree_manager",
    chains,
    indirect=True,
)
def test_calc_next_cycle_range(tree_manager, setup_dynamodb):
    result = calc_next_cycle_range(tree_manager.chain, tree_manager)
    assert result[0] == mock_tree
