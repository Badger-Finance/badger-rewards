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

from helpers.constants import EMISSIONS_CONTRACTS, ETH_BADGER_TREE
from helpers.enums import Network
from rewards.aws.helpers import get_secret
from rewards.classes.TreeManager import TreeManager
from rewards.tree_utils import calc_next_cycle_range
from rewards.tree_utils import get_last_proposed_cycle
from scripts.rewards.utils.propose_rewards import propose_root
from scripts.rewards.utils.approve_rewards import approve_root
from config.singletons import env_config

logger = logging.getLogger("test-cycles-eth")


class MockCycleLogger:
    def __init__(self):
        pass

    def save(self, *args, **kwargs):
        pass

    def set_start_block(self, start):
        pass

    def set_end_block(self, end):
        pass

    def set_content_hash(self, root_hash):
        pass

    def set_merkle_root(self, root):
        pass


def mock_fetch_current_tree(*args, **kwargs):
    return mock_tree


def mock_download_boosts(*args, **kwargs):
    return mock_boosts


def mock_upload_boosts(boosts, chain: str):
    for user in list(boosts["userData"].keys()):
        # will throw key error if multipliers data not added
        boosts["userData"][user]["multipliers"]


def mock_upload_tree(*args, **kwargs):
    pass


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


@pytest.fixture(autouse=True)
def badger_tree(chain, keeper_address):
    accounts[0].transfer(keeper_address, "10 ether", priority_fee="2 gwei")
    with open(f"abis/eth/BadgerTreeV2.json") as fp:
        abi = json.load(fp)
    badger_tree = Contract.from_abi(
        "BadgerTree",
        EMISSIONS_CONTRACTS[chain]["BadgerTree"],
        abi,
    )
    proposer_role = badger_tree.ROOT_PROPOSER_ROLE()
    approver_role = badger_tree.ROOT_VALIDATOR_ROLE()
    admin_role = badger_tree.getRoleAdmin(proposer_role)
    admin = badger_tree.getRoleMember(admin_role, 0)
    accounts[0].transfer(admin, "10 ether", priority_fee="2 gwei")
    badger_tree.grantRole(
        proposer_role, keeper_address, {"from": admin, "priority_fee": "2 gwei"}
    )
    badger_tree.grantRole(
        approver_role, keeper_address, {"from": admin, "priority_fee": "2 gwei"}
    )
    assert badger_tree.hasRole(proposer_role, keeper_address)
    assert badger_tree.hasRole(approver_role, keeper_address)
    return badger_tree


@pytest.fixture
def tree_manager(chain, cycle_account, badger_tree):
    with open(f"abis/eth/BadgerTreeV2.json") as fp:
        abi = json.load(fp)
    tree_manager = TreeManager(chain, cycle_account)
    tree_manager.fetch_current_tree = mock_fetch_current_tree
    tree_manager.w3 = web3
    tree_manager.badger_tree = web3.eth.contract(
        address=EMISSIONS_CONTRACTS[chain]["BadgerTree"], abi=abi
    ).functions

    return tree_manager


@pytest.mark.require_network("hardhat-fork")
def test_propose_root(tree_manager, badger_tree, keeper_address):
    assert keeper_address == tree_manager.approve_account.address
    past_rewards, start_block, end_block = calc_next_cycle_range(
        tree_manager.chain, tree_manager
    )

    pending_hash_before = badger_tree.pendingMerkleContentHash()
    pending_root_before = badger_tree.pendingMerkleRoot()
    timestamp_before = badger_tree.lastProposeTimestamp()

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

    pending_hash_after = badger_tree.pendingMerkleContentHash()
    pending_root_after = badger_tree.pendingMerkleRoot()
    timestamp_after = badger_tree.lastProposeTimestamp()
    assert pending_hash_before != pending_hash_after
    assert pending_root_before != pending_root_after
    assert timestamp_after > timestamp_before


@pytest.mark.require_network("hardhat-fork")
def test_cycle(tree_manager, badger_tree, keeper_address):
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

    proposed_hash = badger_tree.pendingMerkleContentHash()
    proposed_root = badger_tree.pendingMerkleRoot()
    logger.info(f"proposed hash: {proposed_hash}")
    logger.info(f"proposed root: {proposed_root}")

    current_rewards, start_block, end_block = get_last_proposed_cycle(
        tree_manager.chain, tree_manager
    )

    logger.info(f"**Approving Rewards on {tree_manager.chain}**")
    logger.info(f"Calculating rewards between {start_block} and {end_block}")

    approve_root(
        tree_manager.chain,
        start_block,
        end_block,
        current_rewards,
        tree_manager,
    )

    approved_hash = badger_tree.merkleContentHash()
    approved_root = badger_tree.merkleRoot()
    logger.info(f"approved hash: {approved_hash}")
    logger.info(f"approved root: {approved_root}")

    assert proposed_hash == approved_hash
    assert proposed_root == approved_root
