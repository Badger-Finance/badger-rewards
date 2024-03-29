from itertools import zip_longest

from eth_utils import encode_hex
from web3 import Web3

from logging_utils import logger
from rewards.classes.RewardsList import RewardsList

"""
Convert merkle_tree
"""


class MerkleTree:
    def __init__(self, elements):
        self.elements = sorted(set(Web3.keccak(hexstr=el) for el in elements))
        self.layers = MerkleTree.get_layers(self.elements)

    @property
    def root(self):
        return self.layers[-1][0]

    def get_proof(self, el):
        el = Web3.keccak(hexstr=el)
        idx = self.elements.index(el)
        proof = []
        for layer in self.layers:
            pair_idx = idx + 1 if idx % 2 == 0 else idx - 1
            if pair_idx < len(layer):
                proof.append(encode_hex(layer[pair_idx]))
            idx //= 2
        return proof

    @staticmethod
    def get_layers(elements):
        layers = [elements]
        while len(layers[-1]) > 1:
            layers.append(MerkleTree.get_next_layer(layers[-1]))
        return layers

    @staticmethod
    def get_next_layer(elements):
        return [
            MerkleTree.combined_hash(a, b)
            for a, b in zip_longest(elements[::2], elements[1::2])
        ]

    @staticmethod
    def combined_hash(a, b):
        if a is None:
            return b
        if b is None:
            return a
        return Web3.keccak(b"".join(sorted([a, b])))


def rewards_to_merkle_tree(rewards: RewardsList, startBlock, endBlock):
    (nodes, encodedNodes, entries) = rewards.to_merkle_format()

    # For each user, encode their data into a node
    """
    'claims': {
            user: {'index': index, 'amount': hex(amount), 'proof': tree.get_proof(nodes[index])}
            for index, user, amount in elements
        },
    """
    tree = MerkleTree(encodedNodes)
    token_totals = {k: int(v) for k, v in rewards.totals.items()}
    distribution = {
        "merkleRoot": encode_hex(tree.root),
        "cycle": nodes[0]["cycle"],
        "startBlock": str(startBlock),
        "endBlock": str(endBlock),
        "tokenTotals": token_totals,
        "claims": {},
        "metadata": {},
    }

    for entry in entries:
        node = entry["node"]
        encoded = entry["encoded"]
        distribution["claims"][node["user"]] = {
            "index": hex(node["index"]),
            "user": node["user"],
            "cycle": hex(node["cycle"]),
            "tokens": node["tokens"],
            "cumulativeAmounts": node["cumulativeAmounts"],
            "proof": tree.get_proof(encodedNodes[node["index"]]),
            "node": encoded,
        }
    logger.info(f"merkle root: {encode_hex(tree.root)}")

    return distribution
