from rewards.aws.trees import upload_tree
from helpers.constants import CHAIN_IDS
from rewards.aws.trees import download_latest_tree
from rewards.classes.TreeManager import TreeManager
from rewards.aws.helpers import get_secret
from config.singletons import env_config
from eth_account import Account
from rewards.calc_rewards import approve_root, propose_root
from rewards.rewards_utils import merkle_tree_to_rewards_list
from subgraph.queries.setts import last_synced_block
from decouple import config
from eth_account import Account
from web3 import Web3
import json
from eth_utils.hexadecimal import encode_hex


def fix_checksum(chain):
    tree = download_latest_tree(chain)
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )

    rewards = merkle_tree_to_rewards_list(tree)
    tokens = list(tree["tokenTotals"].keys())
    tokens_to_fix = [t for t in tokens if t.islower()]
    for user, claims in rewards.claims.items():
        for token, amount in list(claims.items()):
            if token in tokens_to_fix:
                rewards.decrease_user_rewards(user, token, amount)
                rewards.increase_user_rewards(
                    user, Web3.toChecksumAddress(token), amount
                )

    tree_manager = TreeManager(chain, Account.from_key(cycle_key))
    start_block = int(tree["endBlock"]) + 1
    end_block = start_block

    fixed_tree = tree_manager.convert_to_merkle_tree(rewards, start_block, end_block)

    for token, total_amount in fixed_tree["tokenTotals"].items():
        print(total_amount)
        print(tree["tokenTotals"][token] + tree["tokenTotals"].get(token.lower(), 0))
        assert total_amount == tree["tokenTotals"][token] + tree["tokenTotals"].get(
            token.lower(), 0
        )

    root_hash = Web3.keccak(text=fixed_tree["merkleRoot"])
    chain_id = CHAIN_IDS[chain]
    file_name = f"rewards-{chain_id}-{encode_hex(root_hash)}.json"
    rewards = {
        "merkleTree": fixed_tree,
        "rootHash": root_hash.hex(),
        "fileName": file_name,
        "multiplierData": {},
        "userMultipliers": {},
    }
    with open("fixed.json", "w") as fp:
        json.dump(fixed_tree, fp)

    tx_hash, success = tree_manager.propose_root(rewards)
    if success:
        tx_hash2, approve_success = tree_manager.approve_root(rewards)
        if approve_success:
            upload_tree(
                rewards["fileName"],
                rewards["merkleTree"],
                chain,
                staging=env_config.test or env_config.staging,
            )
