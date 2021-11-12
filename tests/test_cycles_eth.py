import os
import pytest
from brownie import accounts, Contract, web3
from brownie.network.gas.strategies import ExponentialScalingStrategy
from decimal import Decimal
from hexbytes import HexBytes
from web3 import contract
import json
import logging
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

from helpers.constants import EMISSIONS_CONTRACTS
from helpers.enums import Network
from rewards.aws.helpers import get_secret
from rewards.classes.TreeManager import TreeManager
from rewards.tree_utils import calc_next_cycle_range
from scripts.rewards.utils.propose_rewards import propose_root
from config.singletons import env_config

logger = logging.getLogger("test-cycles-eth")


def mock_fetch_current_tree(*args, **kwargs):
    return mock_tree


def mock_download_boosts(*args, **kwargs):
    return mock_boosts


@pytest.fixture(autouse=True)
def mock_fns(monkeypatch):
    monkeypatch.setattr("rewards.calc_rewards.download_boosts", mock_download_boosts)


@pytest.fixture
def chain():
    return Network.Ethereum


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


@pytest.fixture
def tree_manager(chain, cycle_account):
    tree_manager = TreeManager(chain, cycle_account)
    tree_manager.fetch_current_tree = mock_fetch_current_tree
    return tree_manager


@pytest.fixture(autouse=True)
def setup_badger_tree(chain, keeper_address):
    accounts[0].transfer(keeper_address, "10 ether", priority_fee="2 gwei")
    with open(f"abis/eth/BadgerTreeV2.json") as fp:
        abi = json.load(fp)
    badger_tree = Contract.from_abi(
        "BadgerTree",
        EMISSIONS_CONTRACTS[chain]["BadgerTree"],
        abi,
    )
    proposer_role = badger_tree.ROOT_PROPOSER_ROLE()
    admin_role = badger_tree.getRoleAdmin(proposer_role)
    admin = badger_tree.getRoleMember(admin_role, 0)
    accounts[0].transfer(admin, "10 ether", priority_fee="2 gwei")
    badger_tree.grantRole(
        proposer_role, keeper_address, {"from": admin, "priority_fee": "2 gwei"}
    )
    return badger_tree


def test_propose_root(tree_manager):
    past_rewards, start_block, end_block = calc_next_cycle_range(
        tree_manager.chain, tree_manager
    )

    logger.info(
        f"Generating rewards between {start_block} and {end_block} on {tree_manager.chain} chain"
    )
    logger.info(f"**Proposing Rewards on {tree_manager.chain}**")
    logger.info(f"Calculating rewards between {start_block} and {end_block}")
    propose_root(
        tree_manager.chain,
        start_block,
        end_block,
        past_rewards,
        tree_manager,
        save=False,
    )
