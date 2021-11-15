import json
import logging
import os
import pytest
from decimal import Decimal
from hexbytes import HexBytes

from brownie import accounts, Contract, web3
from brownie.network.gas.strategies import ExponentialScalingStrategy
from web3 import contract
from eth_account import Account

from tests.utils import (
    test_address,
    test_key,
    mock_tree,
    mock_boosts,
    set_env_vars,
)

set_env_vars()
os.environ["private"] = test_key

from config.singletons import env_config
from helpers.constants import EMISSIONS_CONTRACTS, ETH_BADGER_TREE, ABI_DIRS
from helpers.enums import Network
from rewards.aws.helpers import get_secret
from rewards.classes.TreeManager import TreeManager
from rewards.tree_utils import calc_next_cycle_range
from rewards.tree_utils import get_last_proposed_cycle
from scripts.rewards.utils.propose_rewards import propose_root
from scripts.rewards.utils.approve_rewards import approve_root
from tests.cycle_utils import mock_badger_tree
from tests.cycle_utils import mock_cycle
from tests.cycle_utils import mock_download_boosts
from tests.cycle_utils import mock_propose_root
from tests.cycle_utils import mock_tree_manager
from tests.cycle_utils import mock_upload_boosts
from tests.cycle_utils import mock_upload_tree
from tests.cycle_utils import MockCycleLogger

logger = logging.getLogger("test-cycles-eth")


@pytest.fixture(autouse=True)
def mock_fns(monkeypatch):
    monkeypatch.setattr("rewards.calc_rewards.download_boosts", mock_download_boosts)
    monkeypatch.setattr("rewards.calc_rewards.upload_boosts", mock_upload_boosts)
    monkeypatch.setattr("rewards.calc_rewards.upload_tree", mock_upload_tree)
    monkeypatch.setattr("rewards.calc_rewards.cycle_logger", MockCycleLogger())


@pytest.fixture(autouse=True)
def set_env_config(monkeypatch):
    env_config.test = False
    env_config.staging = False
    env_config.production = True


@pytest.fixture
def chain():
    return Network.Polygon


@pytest.fixture
def keeper_address():
    return test_address


@pytest.fixture
def cycle_account():
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    return Account.from_key(cycle_key)


@pytest.fixture(autouse=True)
def badger_tree(chain, keeper_address):
    badger_tree = mock_badger_tree(chain, keeper_address, accounts[0])
    return badger_tree


@pytest.fixture
def tree_manager(chain, cycle_account, badger_tree):
    tree_manager = mock_tree_manager(chain, cycle_account, badger_tree)
    return tree_manager


@pytest.mark.require_network("polygon-main-fork")
def test_propose_root(tree_manager, badger_tree, keeper_address):
    mock_propose_root(tree_manager, badger_tree, keeper_address)


@pytest.mark.require_network("polygon-main-fork")
def test_cycle(tree_manager, badger_tree, keeper_address):
    mock_cycle(tree_manager, badger_tree, keeper_address)
