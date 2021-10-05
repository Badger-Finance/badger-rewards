import os
import pytest
import json
from brownie import accounts, Contract, web3
from eth_account import Account
from decimal import Decimal
from hexbytes import HexBytes
from web3 import contract

os.environ["KUBE"] = "False"
os.environ["TEST"] = "True"

from rewards.classes.TreeManager import TreeManager
from tests.utils import test_address, test_key, chains, mock_tree


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
    ["eth"],
    indirect=True,
)
def test_matches_pending_hash(tree_manager):
    pending_hash = tree_manager.badger_tree.pendingMerkleContentHash().call()
    assert tree_manager.matches_pending_hash(pending_hash)

    random_hash = "0xb8ed7da2062b6bdf6f20bcdb4ab35538592216ac70a4bfe986af748603debfd8"
    assert not tree_manager.matches_pending_hash(random_hash)
