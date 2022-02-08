import csv
from decimal import Decimal

from eth_utils.hexadecimal import encode_hex
from web3 import Web3

from config.constants.chain_mappings import CHAIN_IDS
from helpers.enums import Network
from rewards.classes.MerkleTree import rewards_to_merkle_tree
from rewards.classes.RewardsList import RewardsList
from rewards.classes.TreeManager import TreeManager
from rewards.utils.rewards_utils import merkle_tree_to_rewards_list


def add_rewards(rewards_list: RewardsList, file_name):
    reader = csv.DictReader(open(file_name))
    for row in reader:
        print(row)
        amount = Decimal(float(row["amount"]) * 1e18)
        rewards_list.increase_user_rewards(
            row["receiver"], row["token_address"], amount
        )


def rebate(tree, tree_manager: TreeManager):
    chain = Network.Ethereum
    rewards_list = merkle_tree_to_rewards_list(tree)

    rewards_list.cycle += 1

    add_rewards(rewards_list, "rebates/missing_bip75_first_point.csv")
    add_rewards(rewards_list, "rebates/missing_bip75_second_point.csv")

    start_block = int(tree["endBlock"]) + 1
    end_block = start_block
    merkle_tree = rewards_to_merkle_tree(rewards_list, start_block, end_block)
    root_hash = Web3.keccak(text=merkle_tree["merkleRoot"])
    chain_id = CHAIN_IDS[chain]

    file_name = f"rewards-{chain_id}-{encode_hex(root_hash)}.json"

    return {
        "merkleTree": merkle_tree,
        "rootHash": root_hash.hex(),
        "fileName": file_name,
        "multiplierData": {},
        "userMultipliers": {},
    }
