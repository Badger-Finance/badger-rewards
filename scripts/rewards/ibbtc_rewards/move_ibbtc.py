import requests
from eth_utils.hexadecimal import encode_hex
from web3 import Web3

from helpers.constants import CHAIN_IDS, IBBTC_PEAK, TECH_OPS
from helpers.enums import Network
from rewards.classes.MerkleTree import rewards_to_merkle_tree
from rewards.classes.TreeManager import TreeManager
from rewards.utils.rewards_utils import (
    get_claimed_for_token,
    merkle_tree_to_rewards_list,
)


def move_ibbtc(tree, tree_manager: TreeManager):
    chain = Network.Ethereum
    rewards_list = merkle_tree_to_rewards_list(tree)
    BCVXCRV = "0x2B5455aac8d64C14786c3a29858E43b5945819C0"
    BCVX = "0x53C8E199eb2Cb7c01543C137078a038937a68E40"

    peak_data = requests.get(f"https://api.badger.com/v2/reward/tree/{IBBTC_PEAK}").json()
    claimed_for = tree_manager.get_claimed_for(IBBTC_PEAK, [BCVX, BCVXCRV])
    bcvxcrv_claimed_for = get_claimed_for_token(claimed_for, BCVXCRV)
    bcvxcrv_cumulative_amount = peak_data["cumulativeAmounts"][peak_data["tokens"].index(BCVXCRV)] 
    bcvx_claimed_for = get_claimed_for_token(claimed_for, BCVX)
    bcvx_cumulative_amount = peak_data["cumulativeAmounts"][peak_data["tokens"].index(BCVX)]

    bcvxcrv_rewards = bcvxcrv_cumulative_amount - bcvxcrv_claimed_for
    bcvx_rewards = bcvx_cumulative_amount - bcvx_claimed_for

    rewards_list.increase_user_rewards(
        TECH_OPS, BCVX, bcvx_rewards
    )

    rewards_list.decrease_user_rewards(
        peak_data["user"],
        BCVX,
        bcvx_rewards
    )
    rewards_list.cycle += 1
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
