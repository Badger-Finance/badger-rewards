from eth_utils.hexadecimal import encode_hex
from web3 import Web3

from config.constants.addresses import IBBTC_MULTISIG, IBBTC_PEAK, TECH_OPS
from config.constants.chain_mappings import CHAIN_IDS, SETTS
from helpers.enums import Network
from rewards.classes.MerkleTree import rewards_to_merkle_tree
from rewards.classes.TreeManager import TreeManager
from rewards.utils.rewards_utils import (
    get_claimed_for_token,
    get_cumulative_claimable_for_token,
    merkle_tree_to_rewards_list,
)


def move_ibbtc(tree, tree_manager: TreeManager):
    chain = Network.Ethereum
    rewards_list = merkle_tree_to_rewards_list(tree)
    BCVXCRV = SETTS[Network.Ethereum]["cvx_crv"]
    peak_data = tree["claims"][IBBTC_PEAK]
    claimed_for = tree_manager.get_claimed_for(IBBTC_PEAK, [BCVXCRV])
    bcvx_crv_claimed_for = get_claimed_for_token(claimed_for, BCVXCRV)
    bcvx_crv_cumulative_amount = get_cumulative_claimable_for_token(peak_data, BCVXCRV)

    bcvx_crv_rewards = bcvx_crv_cumulative_amount - bcvx_crv_claimed_for


    rewards_list.increase_user_rewards(
        IBBTC_MULTISIG, BCVXCRV, bcvx_crv_rewards
    )

    rewards_list.decrease_user_rewards(
        peak_data["user"],
        BCVXCRV,
        bcvx_crv_rewards
    )

    rewards_list.cycle += 1
    start_block = int(tree["endBlock"]) + 1
    end_block = start_block
    merkle_tree = rewards_to_merkle_tree(rewards_list, start_block, end_block)

    try:
        pre_ibbtc_msig_bcvxcrv = get_cumulative_claimable_for_token(tree["claims"][IBBTC_MULTISIG], BCVXCRV)
    except:
        pre_ibbtc_msig_bcvxcrv = 0
    post_ibbtc_msig_bcvxcrv = get_cumulative_claimable_for_token(merkle_tree["claims"][IBBTC_MULTISIG], BCVXCRV)

    # Make sure total rewards don't change
    #assert merkle_tree["tokenTotals"][BCVXCRV] == tree["tokenTotals"][BCVXCRV]
    assert bcvx_crv_rewards == post_ibbtc_msig_bcvxcrv - pre_ibbtc_msig_bcvxcrv

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
