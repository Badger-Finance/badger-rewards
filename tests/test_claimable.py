import pytest
import json
from eth_account import Account

from badger_api.account import  fetch_all_claimable_balances
from rewards.classes.TreeManager import TreeManager
from tests.utils import test_address, test_key,  mock_tree
from helpers.constants import BOOST_CHAINS

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
    "chain",
    ["eth", "matic", "arbitrum"],
)
def test_fetch_all_claimable_balances(chain):
    print(chain)
    result = fetch_all_claimable_balances(chain)
    assert len(result) > 0


