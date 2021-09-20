from eth_account import Account
import traceback
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
from typing import List
import json

console = Console()


class TreeManager:
    def __init__(self, chain: str, cycle_account: Account):
        self.chain = chain
        self.w3 = env_config.get_web3(chain)
        self.badgerTree = get_badger_tree(chain)
        self.nextCycle = self.get_current_cycle() + 1
        self.rewardsList = RewardsList(self.nextCycle)
        self.propose_account = cycle_account
        self.approve_account = cycle_account
        self.discord_url = get_secret(
            MONITORING_SECRET_NAMES.get(chain, ""),
            "DISCORD_WEBHOOK_URL",
            test=env_config.test,
        )

    def convert_to_merkle_tree(self, rewardsList: RewardsList, start: int, end: int):
        return rewards_to_merkle_tree(rewardsList, start, end)

    def build_function_and_send(self, account, func) -> str:
        options = self.get_tx_options(account)
        console.log(options)
        tx = func.buildTransaction(options)
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction).hex()
        return tx_hash

    def approve_root(self, rewards) -> str:
        console.log("Approving root")
        approve_root_func = self.badgerTree.approveRoot(
            to_bytes(hexstr=rewards["merkleTree"]["merkleRoot"]),
            to_bytes(hexstr=rewards["rootHash"]),
            int(rewards["merkleTree"]["cycle"]),
            int(rewards["merkleTree"]["startBlock"]),
            int(rewards["merkleTree"]["endBlock"]),
        )
        tx_hash = HexBytes(0)
        try:
            tx_hash = self.build_function_and_send(
                self.approve_account, func=approve_root_func
            )
            succeeded, msg = confirm_transaction(
                self.w3,
                tx_hash,
            )
            title = "**Approved Rewards on {}**".format(self.chain)
            approve_info = (
                "TX Hash: {} \n\n Root: {} \n\n Content Hash: {} \n\n".format(
                    tx_hash, rewards["merkleTree"]["merkleRoot"], rewards["rootHash"]
                )
            )
            description = "Calculated rewards between {} and {} \n\n {} ".format(
                int(rewards["merkleTree"]["startBlock"]),
                int(rewards["merkleTree"]["endBlock"]),
                approve_info,
            )
            console.log("Cycle approved : {}".format(tx_hash))
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
                "**FAILED Approve Rewards on {}**".format(self.chain),
                e,
                [],
                "Rewards Bot",
                url=self.discord_url,
            )
            return tx_hash, False
        return tx_hash, True

    def propose_root(self, rewards: dict) -> str:
        console.log("Propose root")
        propose_root_func = self.badgerTree.proposeRoot(
            to_bytes(hexstr=rewards["merkleTree"]["merkleRoot"]),
            to_bytes(hexstr=rewards["rootHash"]),
            int(rewards["merkleTree"]["cycle"]),
            int(rewards["merkleTree"]["startBlock"]),
            int(rewards["merkleTree"]["endBlock"]),
        )
        tx_hash = HexBytes(0)
        try:
            print("propose root function")
            tx_hash = self.build_function_and_send(
                self.propose_account, func=propose_root_func
            )
            print(tx_hash)
            succeeded, msg = confirm_transaction(
                self.w3,
                tx_hash,
            )

            title = "**Proposed Rewards on {}**".format(self.chain)
            propose_info = (
                "TX Hash: {} \n\n Root: {} \n\n Content Hash: {} \n\n".format(
                    tx_hash, rewards["merkleTree"]["merkleRoot"], rewards["rootHash"]
                )
            )
            description = "Calculated rewards between {} and {} \n\n {} ".format(
                int(rewards["merkleTree"]["startBlock"]),
                int(rewards["merkleTree"]["endBlock"]),
                propose_info,
            )
            console.log("Cycle proposed : {}".format(tx_hash))
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
            console.log(f"Error processing harvest tx: {e} \n {traceback.format_exc()}")
            send_message_to_discord(
                "**FAILED Proposed Rewards on {}**".format(self.chain),
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
        fileName = "rewards-{}-{}.json".format(chainId, merkle["contentHash"])
        tree = json.loads(download_tree(fileName, self.chain))
        self.validate_tree(merkle, tree)
        return tree

    def fetch_current_tree(self):
        currentMerkle = self.fetch_current_merkle_data()
        console.log("Current Merkle \n {}".format(currentMerkle))
        return self.fetch_tree(currentMerkle)

    def fetch_pending_tree(self):
        pendingMerkle = self.fetch_pending_merkle_data()
        console.log("Pending Merkle \n {}".format(pendingMerkle))
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
        print(options)
        return options
