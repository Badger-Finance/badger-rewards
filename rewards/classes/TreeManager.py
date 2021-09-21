from logging import root
from eth_account import Account
import traceback

from web3 import contract
from rewards.explorer import get_explorer_url
from helpers.discord import send_message_to_discord
from eth_utils.hexadecimal import encode_hex
from eth_utils import to_bytes
from hexbytes import HexBytes
from config.env_config import env_config
from rewards.classes.MerkleTree import rewards_to_merkle_tree
from rewards.aws.helpers import get_secret
from rewards.aws.trees import download_tree
from helpers.web3_utils import get_badger_tree
from helpers.constants import MONITORING_SECRET_NAMES
from rewards.classes.RewardsList import RewardsList
from rewards.tx_utils import (
    get_effective_gas_price,
    get_priority_fee,
    confirm_transaction,
    get_gas_price_of_tx,
)
from rich.console import Console
from typing import List, Tuple
import json

console = Console()


class TreeManager:
    def __init__(self, chain: str):
        self.chain = chain
        self.w3 = env_config.get_web3(chain)
        self.badgerTree = get_badger_tree(chain)
        self.nextCycle = self.get_current_cycle() + 1
        self.rewardsList = RewardsList(self.nextCycle)
        cycle_key = get_secret(
            "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
            "private",
            assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
            test=env_config.test,
        )
        console.print("successfully got cycle_key")
        self.propose_account = Account.from_key(cycle_key)
        self.approve_account = Account.from_key(cycle_key)
        self.discord_url = get_secret(
            MONITORING_SECRET_NAMES.get(chain, ""),
            "DISCORD_WEBHOOK_URL",
            test=env_config.test,
        )

    def convert_to_merkle_tree(self, rewardsList: RewardsList, start: int, end: int):
        return rewards_to_merkle_tree(rewardsList, start, end)

    def build_function_and_send(self, account, func) -> str:
        options = self.get_tx_options(account)
        tx = func.buildTransaction(options)
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction).hex()
        return tx_hash

    def approve_root(self, rewards) -> Tuple[str, bool]:
        console.log("Approving root")
        return self.manage_root(rewards, self.badgerTree.approveRoot, approve=True)

    def propose_root(self, rewards):
        console.log("Proposing root")
        return self.manage_root(rewards, self.badgerTree.proposeRoot, approve=False)

    def manage_root(self, rewards, contract_function, approve):
        root_hash = rewards["rootHash"]
        merkle_root = rewards["merkleTree"]["merkleRoot"]
        start_block = rewards["merkleTree"]["startBlock"]
        end_block = rewards["merkleTree"]["endBlock"]
        root_func = contract_function(
            to_bytes(hexstr=merkle_root),
            to_bytes(hexstr=root_hash),
            int(rewards["merkleTree"]["cycle"]),
            int(start_block),
            int(end_block),
        )

        tx_hash = HexBytes(0)
        try:
            tx_hash = self.build_function_and_send(self.approve_account, func=root_func)
            succeeded, msg = confirm_transaction(
                self.w3,
                tx_hash,
            )
            action = "Approved" if approve else "Proposed"
            title = f"**{action} Rewards on {self.chain}**"
            approve_info = f"TX Hash: {tx_hash} \n\n Root: {merkle_root} \n\n Content Hash: {root_hash} \n\n"
            description = f"Calculated rewards between {start_block} and {end_block} \n\n {approve_info} "
            console.log(f"Cycle {action.lower()} : {tx_hash}")

            if succeeded:
                gas_price_of_tx = get_gas_price_of_tx(self.w3, self.chain, tx_hash)
                console.log(f"got gas price of tx: {gas_price_of_tx}")
                send_message_to_discord(
                    title,
                    description,
                    [
                        {
                            "name": "Completed Transaction",
                            "value": get_explorer_url(self.chain, tx_hash),
                            "inline": True,
                        },
                        {
                            "name": "Gas Cost",
                            "value": f"${round(get_gas_price_of_tx(self.w3, self.chain, tx_hash), 2)}",
                            "inline": True,
                        },
                    ],
                    "Rewards Bot",
                    url=self.discord_url,
                )
            else:
                send_message_to_discord(
                    title,
                    description,
                    [
                        {
                            "name": "Pending Transaction",
                            "value": get_explorer_url(self.chain, tx_hash),
                            "inline": True,
                        }
                    ],
                    "Rewards Bot",
                    url=self.discord_url,
                )
        except Exception as e:
            console.log(f"Error processing harvest tx: {e}")
            send_message_to_discord(
                f"**FAILED {action} Rewards on {self.chain}**",
                e,
                [],
                "Rewards Bot",
                url=self.discord_url,
            )
            return tx_hash, False
        return tx_hash, True

    def get_current_cycle(self) -> str:
        return self.badgerTree.currentCycle().call()

    def get_claimable_for(self, user: str, tokens: List[str], cumAmounts: List[int]):
        return self.badgerTree.getClaimableFor(user, tokens, cumAmounts).call()

    def has_pending_root(self) -> bool:
        return self.badgerTree.hasPendingRoot().call()

    def fetch_tree(self, merkle):
        chainId = self.w3.eth.chain_id
        fileName = f"rewards-{chainId}-{merkle['contentHash']}.json"
        tree = json.loads(download_tree(fileName, self.chain))
        self.validate_tree(merkle, tree)
        return tree

    def fetch_current_tree(self):
        currentMerkle = self.fetch_current_merkle_data()
        console.log(f"Current Merkle \n {currentMerkle}")
        return self.fetch_tree(currentMerkle)

    def fetch_pending_tree(self):
        pendingMerkle = self.fetch_pending_merkle_data()
        console.log(f"Pending Merkle \n {pendingMerkle}")
        return self.fetch_tree(pendingMerkle)

    def validate_tree(self, merkle, tree):
        # Invariant: merkle should have same root as latest
        assert tree["merkleRoot"] == merkle["root"]
        lastUpdatePublish = int(merkle["blockNumber"])
        lastUpdate = int(tree["endBlock"])
        assert lastUpdatePublish > lastUpdate
        # Ensure file tracks block within 1 day of upload
        # assert abs(lastUpdate - lastUpdatePublish) < 6500

    def fetch_current_merkle_data(self):
        root = self.badgerTree.merkleRoot().call()
        contentHash = self.badgerTree.merkleContentHash().call()
        return {
            "root": encode_hex(root),
            "contentHash": encode_hex(contentHash),
            "lastUpdateTime": self.badgerTree.lastPublishTimestamp().call(),
            "blockNumber": int(self.badgerTree.lastPublishBlockNumber().call()),
        }

    def fetch_pending_merkle_data(self):
        root = self.badgerTree.pendingMerkleRoot().call()
        pendingContentHash = self.badgerTree.pendingMerkleContentHash().call()
        return {
            "root": encode_hex(root),
            "contentHash": encode_hex(pendingContentHash),
            "lastUpdateTime": self.badgerTree.lastProposeTimestamp().call(),
            "blockNumber": int(self.badgerTree.lastProposeBlockNumber().call()),
        }

    def last_propose_end_block(self) -> int:
        return self.badgerTree.lastProposeEndBlock().call()

    def last_publish_end_block(self) -> int:
        return self.badgerTree.lastPublishEndBlock().call()

    def last_propose_start_block(self) -> int:
        return self.badgerTree.lastProposeStartBlock().call()

    def get_tx_options(self, account: Account) -> dict:
        options = {
            "nonce": self.w3.eth.get_transaction_count(account.address),
            "from": account.address,
        }
        if self.chain == "eth":
            options["maxPriorityFeePerGas"] = get_priority_fee(self.w3)
            options["maxFeePerGas"] = get_effective_gas_price(self.w3, self.chain)
            options["gas"] = 200000
        if self.chain == "arbitrum":
            options["gas"] = 3000000
            # options["gasPrice"] = get_effective_gas_price(self.w3, self.chain)
        else:
            options["gasPrice"] = get_effective_gas_price(self.w3, self.chain)
        return options
