from rewards.classes.MerkleTree import rewards_to_merkle_tree
from rewards.aws.trees import download_tree
from helpers.constants import BADGER_TREE
from helpers.web3_utils import make_contract
from rewards.classes.RewardsList import RewardsList
from helpers.web3_utils import make_contract
from rich.console import Console
import json
from config.env_config import env_config

console = Console()


class TreeManager:
    def __init__(self, chain: str, start: int, end: int):
        self.chain = chain
        self.start = start
        self.end = end
        self.badgerTree = make_contract(BADGER_TREE[self.chain], abiName="BadgerTreeV2", chain=chain)
        self.nextCycle = self.get_current_cycle() + 1
        self.rewardsList = RewardsList(self.nextCycle)

    def convert_to_merkle_tree(self, rewardsList):
        return rewards_to_merkle_tree(rewardsList, self.start, self.end)

    def approve_root(self, rewards):
        self.badgerTree.functions.approveRoot(
        ).call()

    def propose_root(self):
        pass

    def get_current_cycle(self):
        return self.badgerTree.functions.currentCycle().call()
    
    def has_pending_root(self):
        return self.badgerTree.functions.hasPendingRoot().call()
    
    def fetch_tree(self, merkle):
        console.log(merkle)
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
        #assert lastUpdatePublish > lastUpdate
        # Ensure file tracks block within 1 day of upload
        #assert abs(lastUpdate - lastUpdatePublish) < 6500
    
    def fetch_current_merkle_data(self):
        root = self.badgerTree.functions.merkleRoot().call()
        contentHash = self.badgerTree.functions.merkleContentHash().call()
        return {
            "root": env_config.get_web3().toHex(root),
            "contentHash": env_config.get_web3().toHex(contentHash),
            "lastUpdateTime": self.badgerTree.functions.lastPublishTimestamp().call(),
            "blockNumber": int(self.badgerTree.functions.lastPublishBlockNumber().call())
        }
    
    def fetch_pending_merkle_data(self):
        root = self.badgerTree.functions.merkleRoot.call()
        pendingContentHash = self.badgerTree.functions.pendingMerkleContentHash().call()
        return {
            "root": env_config.get_web3().toHex(root),
            "contentHash": env_config.get_web3().toHex(pendingContentHash),
            "lastUpdateTime": self.badgerTree.functions.lastProposeTimestamp().call(),
            "blockNumber": int(self.badgerTree.functions.lastProposeBlockNumber().call())
        }
         