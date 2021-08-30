from helpers.discord import send_message_to_discord
from eth_utils.hexadecimal import encode_hex
from eth_utils import to_bytes
from config.env_config import env_config
from rewards.classes.MerkleTree import rewards_to_merkle_tree
from rewards.aws.trees import download_tree
from helpers.web3_utils import get_badger_tree
from rewards.classes.RewardsList import RewardsList
from rich.console import Console
from typing import List
import json

console = Console()


class TreeManager:
    def __init__(self, chain: str):
        self.chain = chain
        self.w3 = env_config.get_web3(chain)
        self.badgerTree = get_badger_tree(chain)
        self.nextCycle = self.get_current_cycle() + 1
        self.rewardsList = RewardsList(self.nextCycle)

    def convert_to_merkle_tree(self, rewardsList: RewardsList, start: int, end: int):
        return rewards_to_merkle_tree(rewardsList, start, end)

    def approve_root(self, rewards) -> str:
        console.log("Approving root")
        approveRootFunc = self.badgerTree.functions.approveRoot(
            to_bytes(hexstr=rewards["merkleTree"]["merkleRoot"]),
            to_bytes(hexstr=rewards["rootHash"]),
            int(rewards["merkleTree"]["cycle"]),
            int(rewards["merkleTree"]["startBlock"]),
            int(rewards["merkleTree"]["endBlock"])
        )
        approveRootTx = approveRootFunc.buildTransaction({
            'chainId': self.w3.eth.chain_id,
            'gasPrice': self.w3.toWei('1', 'gwei'),
            'gas': 200000,
            'nonce': self.w3.eth.get_transaction_count(env_config.approveAccount.address)
        })
        signedTx = self.w3.eth.account.sign_transaction(
            approveRootTx,
            private_key=env_config.approveAccount.key
        )
        txHash = self.w3.eth.send_raw_transaction(signedTx.rawTransaction).hex()
        send_message_to_discord(
            "**Approved Rewards on {}**".format(self.chain),
            "Calculated rewards between {} and {} \n TX Hash: {} ".format(
                int(rewards["merkleTree"]["startBlock"]),
                int(rewards["merkleTree"]["endBlock"]),
                txHash,
            ),
            [],
            "Rewards Bot",
        )
        return txHash

    def propose_root(self, rewards) -> str:
        console.log("Propose root")
        proposeRootFunc = self.badgerTree.functions.proposeRoot(
            to_bytes(hexstr=rewards["merkleTree"]["merkleRoot"]),
            to_bytes(hexstr=rewards["rootHash"]),
            int(rewards["merkleTree"]["cycle"]),
            int(rewards["merkleTree"]["startBlock"]),
            int(rewards["merkleTree"]["endBlock"])
        )
        proposeRootTx = proposeRootFunc.buildTransaction({
            'chainId': self.w3.eth.chain_id,
            'gasPrice': self.w3.toWei('1', 'gwei'),
            'gas': 200000,
            'nonce': self.w3.eth.get_transaction_count(env_config.proposeAccount.address)
        })
        signedTx = self.w3.eth.account.sign_transaction(
            proposeRootTx,
            private_key=env_config.proposeAccount.key
        )
        txHash = self.w3.eth.send_raw_transaction(signedTx.rawTransaction).hex()
        console.log("Cycle proposed : {}".format(txHash))
        send_message_to_discord(
            "**Proposed Rewards on {}**".format(self.chain),
            "Calculated rewards between {} and {} \n TX Hash: {} ".format(
                int(rewards["merkleTree"]["startBlock"]),
                int(rewards["merkleTree"]["endBlock"]),
                txHash,
            ),
            [],
            "Rewards Bot",
        )
        return txHash

    def get_current_cycle(self) -> str:
        return self.badgerTree.functions.currentCycle().call()
    
    def get_claimable_for(self, user: str, tokens: List[str], cumAmounts: List[int]):
        return self.badgerTree.functions.getClaimableFor(
            user,
            tokens,
            cumAmounts 
        ).call()
        

    def has_pending_root(self) -> bool:
        return self.badgerTree.functions.hasPendingRoot().call()

    def fetch_tree(self, merkle):
        chainId = self.w3.eth.chain_id
        fileName = "rewards-{}-{}.json".format(chainId,merkle["contentHash"])
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
        # assert lastUpdatePublish > lastUpdate
        # Ensure file tracks block within 1 day of upload
        # assert abs(lastUpdate - lastUpdatePublish) < 6500

    def fetch_current_merkle_data(self):
        root = self.badgerTree.functions.merkleRoot().call()
        contentHash = self.badgerTree.functions.merkleContentHash().call()
        return {
            "root": encode_hex(root),
            "contentHash": encode_hex(contentHash),
            "lastUpdateTime": self.badgerTree.functions.lastPublishTimestamp().call(),
            "blockNumber": int(
                self.badgerTree.functions.lastPublishBlockNumber().call()
            ),
        }

    def fetch_pending_merkle_data(self):
        root = self.badgerTree.functions.pendingMerkleRoot().call()
        pendingContentHash = self.badgerTree.functions.pendingMerkleContentHash().call()
        return {
            "root": encode_hex(root),
            "contentHash": encode_hex(pendingContentHash),
            "lastUpdateTime": self.badgerTree.functions.lastProposeTimestamp().call(),
            "blockNumber": int(
                self.badgerTree.functions.lastProposeBlockNumber().call()
            ),
        }

    def last_propose_end_block(self) -> int:
        return self.badgerTree.functions.lastProposeEndBlock().call()

    def last_propose_start_block(self) -> int:
        return self.badgerTree.functions.lastProposeStartBlock().call()
