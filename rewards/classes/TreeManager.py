from re import I
from helpers.constants import PROPOSER_ADDRESS
from eth_utils.hexadecimal import encode_hex
from eth_utils import to_bytes
from config.env_config import env_config
from rewards.classes.MerkleTree import rewards_to_merkle_tree
from rewards.aws.trees import download_tree
from helpers.web3_utils import get_badger_tree
from rewards.classes.RewardsList import RewardsList
from rich.console import Console
import json

console = Console()


class TreeManager:
    def __init__(self, chain: str):
        self.chain = chain
        self.badgerTree = get_badger_tree(chain)
        self.nextCycle = self.get_current_cycle() + 1
        self.rewardsList = RewardsList(self.nextCycle)

    def convert_to_merkle_tree(self, rewardsList, start, end):
        return rewards_to_merkle_tree(rewardsList, start, end)

    def approve_root(self, rewards):
        console.log("Approving root")
        self.badgerTree.functions.approveRoot(
            to_bytes(hexstr=rewards["merkleTree"]["merkleRoot"]),
            to_bytes(hexstr=rewards["rootHash"]),
            int(rewards["merkleTree"]["cycle"]),
            int(rewards["merkleTree"]["startBlock"]),
            int(rewards["merkleTree"]["endBlock"])
        ).call({"from": PROPOSER_ADDRESS, "gasPrice": '200000000000'})

    def propose_root(self, rewards):
        console.log("Propose root")
        self.badgerTree.functions.proposeRoot(
            to_bytes(hexstr=rewards["merkleTree"]["merkleRoot"]),
            to_bytes(hexstr=rewards["rootHash"]),
            int(rewards["merkleTree"]["cycle"]),
            int(rewards["merkleTree"]["startBlock"]),
            int(rewards["merkleTree"]["endBlock"])
        ).call({"from": PROPOSER_ADDRESS, "gasPrice": '200000000000'})

    def get_current_cycle(self):
        return self.badgerTree.functions.currentCycle().call()

    def has_pending_root(self):
        return self.badgerTree.functions.hasPendingRoot().call()

    def fetch_tree(self, merkle):
        fileName = "rewards-1-{}.json".format(merkle["contentHash"])
        tree = json.loads(download_tree(fileName, self.chain))
        self.validate_tree(merkle, tree)
        return tree

    def fetch_current_tree(self):
        currentMerkle = self.fetch_current_merkle_data()
        return self.fetch_tree(currentMerkle)

    def fetch_pending_tree(self):
        pendingMerkle = self.fetch_pending_merkle_data()
        self.fetch_tree(pendingMerkle)

    def validate_tree(self, merkle, tree):
        # Invariant: merkle should have same root as latest
        console.log(merkle)
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
        root = self.badgerTree.functions.merkleRoot().call()
        pendingContentHash = self.badgerTree.functions.pendingMerkleContentHash().call()
        return {
            "root": encode_hex(root),
            "contentHash": encode_hex(pendingContentHash),
            "lastUpdateTime": self.badgerTree.functions.lastProposeTimestamp().call(),
            "blockNumber": int(
                self.badgerTree.functions.lastProposeBlockNumber().call()
            ),
        }
