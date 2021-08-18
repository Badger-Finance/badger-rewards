from rewards.aws.trees import download_tree
from helpers.constants import BADGER_TREE
from helpers.web3_utils import make_contract
from rewards.classes.RewardsList import RewardsList
from helpers.web3_utils import make_contract
from rich.console import Console
import json

console = Console()


class TreeManager:
    def __init__(self, chain: str, start: int, end: int):
        self.chain = chain
        self.start = start
        self.end = end
        self.badgerTree = make_contract(BADGER_TREE[self.chain], abiName="BadgerTreeV2", chain=chain)
        self.nextCycle = self.get_current_cycle() + 1
        self.rewardsList = RewardsList(self.nextCycle)

    def convert_to_merkle_tree(self):
        pass

    def approve_root(self):
        pass

    def propose_root(self):
        pass

    def get_current_cycle(self):
        return self.badgerTree.functions.currentCycle().call()

    def fetch_current_tree(self):
        merkle = self.fetch_current_merkle_data()
        fileName = "rewards-1-{}.json".format(str(merkle["contentHash"]))
        currentTree = json.loads(download_tree(fileName))
        self.validate_tree(merkle, currentTree)
        return currentTree
    
    def fetch_pending_tree(self):
        merkle = self.fetch_pending_merkle_data()
        fileName = "rewards-1-{}.json".format(str(merkle["contentHash"]))
        pendingTree = json.loads(download_tree(fileName))
        self.validate_tree(merkle, pendingTree)
        return pendingTree
    
    def validate_tree(self, merkle, tree):
        # Invariant: merkle should have same root as latest
        assert tree["merkleRoot"] == merkle["root"]
        lastUpdatePublish = merkle["blockNumber"]
        lastUpdate = int(tree["endBlock"])
        assert lastUpdatePublish > lastUpdate
        # Ensure file tracks block within 1 day of upload
        assert abs(lastUpdate - lastUpdatePublish) < 6500
    
    def fetch_current_merkle_data(self):
        return {
            "root": self.badgerTree.functions.merkleRoot().call(),
            "contentHash": self.badgerTree.functions.merkleContentHash().call(),
            "lastUpdateTime": self.badgerTree.functions.lastPublishTimestamp.call(),
            "blockNumber": int(self.badgerTree.functions.lastPublishBlockNumber.call())
        }
    
    def fetch_pending_merkle_data(self):
         return {
            "root": self.badgerTree.functions.pendingMerkleRoot().call(),
            "contentHash": self.badgerTree.functions.pendingMerkleContentHash().call(),
            "lastUpdateTime": self.badgerTree.functions.lastProposeTimestamp.call(),
            "blockNumber": int(self.badgerTree.functions.lastProposeBlockNumber.call())
        }
         