import json
from decimal import Decimal

from eth_utils.hexadecimal import encode_hex
from web3 import Web3

from helpers.constants import CHAIN_IDS
from rewards.classes.MerkleTree import rewards_to_merkle_tree
from rewards.utils.rewards_utils import merkle_tree_to_rewards_list


def fix(tree, tree_manager):
    balance_changes = json.load(open("balance_changes.json"))
    r_list = merkle_tree_to_rewards_list(tree)
    startBlock = int(tree["endBlock"]) + 1
    endBlock = startBlock
    for user, token_data in balance_changes.items():
        for token, amount in token_data.items():
            r_list.decrease_user_rewards(user, token, Decimal(amount))

    new_tree = rewards_to_merkle_tree(r_list, startBlock, endBlock)
    root_hash = Web3.keccak(text=new_tree["merkleRoot"])
    chain_id = CHAIN_IDS[tree_manager.chain]

    file_name = f"rewards-{chain_id}-{encode_hex(root_hash)}.json"
    return {
        "merkleTree": new_tree,
        "rootHash": root_hash.hex(),
        "fileName": file_name,
        "multiplierData": {},
        "userMultipliers": {},
    }

