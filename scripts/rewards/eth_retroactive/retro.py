import json

from eth_utils.hexadecimal import encode_hex
from web3 import Web3

from helpers.constants import CHAIN_IDS
from helpers.enums import Network
from rewards.classes.MerkleTree import rewards_to_merkle_tree
from rewards.utils.rewards_utils import merkle_tree_to_rewards_list


def retro_cycle(tree):
    chain = Network.Ethereum
    affected_users = json.load(open("affected_users.json"))
    rewards_list = merkle_tree_to_rewards_list(tree)
    for addr, data in affected_users.items():
        for token, balance in data.items():
            rewards_list.increase_user_rewards(
                addr, token, abs(balance)
            )
    start_block = int(tree["endBlock"]) + 1
    end_block = start_block
    merkle_tree = rewards_to_merkle_tree(rewards_list, start_block, end_block)
    root_hash = Web3.keccak(text=merkle_tree["merkleRoot"])
    chain_id = CHAIN_IDS[chain]

    file_name = f"rewards-{chain_id}-{encode_hex(root_hash)}.json"

    return {
        "merkleTree": merkle_tree,
        "roothash": root_hash.hex(),
        "fileName": file_name,
        "multiplierData": {},
        "userMultipliers": {}
    }
