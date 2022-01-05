import logging
import os

import pytest
from brownie import accounts
from eth_account import Account

from tests.utils import set_env_vars, test_address, test_key

set_env_vars()
os.environ["private"] = test_key

from config.singletons import env_config
from helpers.enums import Network
from rewards.aws.helpers import get_secret
from tests.test_utils.cycle_utils import (
    MockCycleLogger,
    mock_badger_tree,
    mock_cycle,
    mock_download_boosts,
    mock_tree_manager,
    mock_upload_boosts,
    mock_upload_tree,
)

logger = logging.getLogger("test-cycles-eth")


@pytest.fixture(autouse=True)
def mock_fns(monkeypatch):
    monkeypatch.setattr("rewards.calc_rewards.download_boosts", mock_download_boosts)
    monkeypatch.setattr("rewards.calc_rewards.download_proposed_boosts", mock_download_boosts)
    monkeypatch.setattr("rewards.calc_rewards.upload_boosts", mock_upload_boosts)
    monkeypatch.setattr("rewards.calc_rewards.upload_proposed_boosts", mock_upload_boosts)
    monkeypatch.setattr("rewards.calc_rewards.upload_tree", mock_upload_tree)
    monkeypatch.setattr("rewards.calc_rewards.cycle_logger", MockCycleLogger())


@pytest.fixture(autouse=True)
def set_env_config(monkeypatch):
    env_config.test = False
    env_config.staging = False
    env_config.production = True


@pytest.fixture
def chain():
    return Network.Arbitrum


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


@pytest.mark.require_network("hardhat-arbitrum-fork")
def test_cycle(tree_manager, badger_tree, keeper_address):
    mock_cycle(tree_manager, badger_tree, keeper_address)
