from rewards.snapshot.claims_snapshot import claims_snapshot
from subgraph.queries.setts import last_synced_block
from badger_api.requests import fetch_token
from helpers.constants import ETH_BADGER_TREE
from helpers.web3_utils import make_token
import json
from rich.console import Console
from helpers.enums import Network

console = Console()

if __name__ == "__main__":
    chain = Network.Ethereum
    snapshots = claims_snapshot(Network.Ethereum, last_synced_block(chain))

    console.log("claim snapshot taken ")

    for token, snap in snapshots.items():
        t = make_token(token, chain)
        name = t.name().call()
        tree_balance = t.balanceOf(ETH_BADGER_TREE).call() / 1e18
        total = float(snap.total_balance())
        console.log(name)
        console.log("Tree Balance: {}".format(tree_balance))
        console.log("Claimable Balance: {}".format(total))
        console.log("Deficit: {}".format(tree_balance - total))
        console.log("\n")
