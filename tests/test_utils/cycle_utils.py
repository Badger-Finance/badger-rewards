import json
import logging
from decimal import Decimal
from typing import Dict

from brownie import Contract, web3
from eth_account import Account

from config.constants.chain_mappings import ABI_DIRS, EMISSIONS_CONTRACTS
from helpers.enums import Network
from rewards.classes.TreeManager import TreeManager
from rewards.utils.tree_utils import calc_next_cycle_range, get_last_proposed_cycle
from scripts.rewards.utils.approve_rewards import approve_root
from scripts.rewards.utils.propose_rewards import propose_root
from tests.utils import mock_boosts, mock_tree

logger = logging.getLogger("cycle-utils")


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
    keys = list(boosts["userData"].keys())
    for user in keys:
        for _, v in boosts["userData"][user].items():
            assert type(v) != Decimal
            assert json.dumps(v)
    with open(f"{chain}-boosts.json", "w") as f:
        json.dump(boosts, f)


def mock_upload_tree(
    file_name: str,
    data: Dict,
    chain: str,
    bucket: str = "badger-json",
    staging: bool = False,
):
    with open(f"{chain}-tree.json", "w") as f:
        json.dump(data, f)


def mock_badger_tree(chain: Network, keeper_address: str, account: Account):
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

    if chain == Network.Ethereum:
        account.transfer(admin, "10 ether", priority_fee="2 gwei")

        badger_tree.grantRole(
            proposer_role, keeper_address, {"from": admin, "priority_fee": "2 gwei"}
        )
        badger_tree.grantRole(
            approver_role, keeper_address, {"from": admin, "priority_fee": "2 gwei"}
        )
    else:
        badger_tree.grantRole(proposer_role, keeper_address, {"from": admin})
        badger_tree.grantRole(approver_role, keeper_address, {"from": admin})
    assert badger_tree.hasRole(proposer_role, keeper_address)
    assert badger_tree.hasRole(approver_role, keeper_address)
    return badger_tree


def mock_tree_manager(chain, cycle_account, badger_tree):
    with open(f"abis/eth/BadgerTreeV2.json") as fp:
        abi = json.load(fp)
    tree_manager = TreeManager(chain, cycle_account)
    tree_manager.fetch_current_tree = mock_fetch_current_tree
    tree_manager.w3 = web3
    tree_manager.badger_tree = web3.eth.contract(
        address=EMISSIONS_CONTRACTS[chain]["BadgerTree"], abi=abi
    ).functions
    return tree_manager


def mock_cycle(tree_manager, badger_tree, keeper_address):
    pending_hash_before = badger_tree.pendingMerkleContentHash()
    pending_root_before = badger_tree.pendingMerkleRoot()
    timestamp_before = badger_tree.lastProposeTimestamp()

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
    timestamp_after = badger_tree.lastProposeTimestamp()
    logger.info(f"proposed hash: {proposed_hash}")
    logger.info(f"proposed root: {proposed_root}")

    assert pending_hash_before != proposed_hash
    assert pending_root_before != proposed_root
    assert timestamp_after > timestamp_before

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
