import json

from eth_utils.hexadecimal import encode_hex
from web3 import Web3

from helpers.constants import CHAIN_IDS, TECH_OPS
from helpers.enums import Network
from rewards.classes.MerkleTree import rewards_to_merkle_tree
from rewards.classes.TreeManager import TreeManager
from rewards.utils.rewards_utils import merkle_tree_to_rewards_list


def move_ibbtc(tree, tree_manager: TreeManager):
    chain = Network.Ethereum
    rewards_list = merkle_tree_to_rewards_list(tree)
    BCVXCRV = "0x2B5455aac8d64C14786c3a29858E43b5945819C0"
    BCVX = "0x53C8E199eb2Cb7c01543C137078a038937a68E40"

    peak_data =  {
            "index": "0x130d",
            "user": "0x41671BA1abcbA387b9b2B752c205e22e916BE6e3",
            "cycle": "0xe93",
            "tokens": [
                "0x2B5455aac8d64C14786c3a29858E43b5945819C0",
                "0x53C8E199eb2Cb7c01543C137078a038937a68E40",
                "0x3472A5A71965499acd81997a54BBA8D852C6E53d",
                "0x798D1bE841a82a273720CE31c822C61a67a601C3"
            ],
            "cumulativeAmounts": [
                "47433677792475081612856",
                "17698458072579331418028",
                "1075859383293781550483",
                "4684115086440894307928604356080202044898819615861946914098633464872960"
            ],
    }
    bcvxcrv_rewards = peak_data["cumulativeAmounts"][peak_data["tokens"].index(BCVXCRV)]
    bcvx_rewards = peak_data["cumulativeAmounts"][peak_data["tokens"].index(BCVX)]

    rewards_list.increase_user_rewards(
        TECH_OPS, BCVX, bcvx_rewards
    )
    rewards_list.increase_user_rewards(
        TECH_OPS, BCVXCRV, bcvxcrv_rewards
    )

    rewards_list.decrease_user_rewards(
        peak_data["user"],
        BCVX,
        bcvx_rewards
    )
    rewards_list.decrease_user_rewards(
        peak_data["user"],
        bcvxcrv_rewards,
        bcvx_rewards
    )
    rewards_list.cycle +=1
    
            
    start_block = int(tree["endBlock"]) + 1
    end_block = start_block
    merkle_tree = rewards_to_merkle_tree(rewards_list, start_block, end_block)
    # Make sure total rewards don't change
    assert merkle_tree["tokenTotals"][BCVX] == tree["tokenTotals"][BCVX]
    assert merkle_tree["tokenTotals"][BCVXCRV] == tree["tokenTotals"][BCVXCRV]

    root_hash = Web3.keccak(text=merkle_tree["merkleRoot"])
    chain_id = CHAIN_IDS[chain]

    file_name = f"rewards-{chain_id}-{encode_hex(root_hash)}.json"

    return {
        "merkleTree": merkle_tree,
        "rootHash": root_hash.hex(),
        "fileName": file_name,
        "multiplierData": {},
        "userMultipliers": {}
    }
