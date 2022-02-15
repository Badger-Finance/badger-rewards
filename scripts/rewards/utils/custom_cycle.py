from web3 import Web3
import json
from config.constants.chain_mappings import CHAIN_IDS
from eth_utils.hexadecimal import encode_hex
from eth_account import Account
from config.env_config import EnvConfig
from config.singletons import env_config
from helpers.enums import Network
from rewards.aws.helpers import get_secret
from rewards.aws.trees import download_latest_tree, upload_tree
from decouple import config
from rewards.classes.TreeManager import TreeManager
from rewards.classes.MerkleTree import rewards_to_merkle_tree
from typing import Callable

def custom_propose(chain: Network, custom_calc: Callable, custom_test: Callable):
    tree = download_latest_tree(chain)
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    propose_tree_manager = TreeManager(chain, Account.from_key(cycle_key))

    rewards_data = custom_calculation(tree, propose_tree_manager, chain, custom_calc, custom_test)
    if env_config.production:
        tx_hash, succeded = propose_tree_manager.propose_root(rewards_data)


def custom_approve(chain: Network, custom_calc: Callable, custom_test: Callable):
    tree = download_latest_tree(chain)
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    approve_tree_manager = TreeManager(chain, Account.from_key(cycle_key))

    rewards_data = custom_calculation(tree, approve_tree_manager, chain, custom_calc, custom_test)
    if env_config.production:
        tx_hash, succeded = approve_tree_manager.approve_root(rewards_data)
        if succeded:
            upload_tree(
                rewards_data["fileName"],
                rewards_data["merkleTree"],
                chain,
                staging=env_config.test or env_config.staging,
            )


def custom_eth_approve(chain, custom_calc: Callable, custom_test: Callable):
    tree = download_latest_tree(chain)
    key_decrypt_password = get_secret(
        "DECRYPT_PASSWORD_ARN",
        "DECRYPT_PASSWORD_KEY",
        region_name="us-west-2",
        kube=False,
    )
    with open(config("KEYFILE")) as key_file:
        key_file_json = json.load(key_file)

    cycle_key = Account.decrypt(key_file_json, key_decrypt_password)

    approve_tree_manager = TreeManager(chain, Account.from_key(cycle_key))
    rewards_data = custom_calculation(tree, approve_tree_manager, chain, custom_calc, custom_test)
    if env_config.production:
        tx_hash, succeded = approve_tree_manager.approve_root(rewards_data)
        if succeded:
            upload_tree(
                rewards_data["fileName"],
                rewards_data["merkleTree"],
                chain,
                staging=env_config.test or env_config.staging,
            )


def custom_calculation(tree, tree_manager, chain, custom_calc: Callable, custom_test: Callable = None):

    rewards_list = custom_calc(tree, tree_manager)
    start_block = int(tree["endBlock"]) + 1
    end_block = start_block
    merkle_tree = rewards_to_merkle_tree(rewards_list, start_block, end_block)
    assert custom_test(tree, merkle_tree)
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
