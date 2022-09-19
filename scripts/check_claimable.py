import json

from config.constants.addresses import ETH_BADGER_TREE
from helpers.enums import Network
from helpers.web3_utils import make_token
from logging_utils import logger
from rewards.snapshot.claims_snapshot import claims_snapshot
from subgraph.queries.setts import last_synced_block

if __name__ == "__main__":
    chain = Network.Ethereum
    snapshots = claims_snapshot(Network.Ethereum, last_synced_block(chain))

    logger.info("claim snapshot taken ")

    deficit = {}

    for token, snap in snapshots.items():
        t = make_token(token, chain)
        name = t.name().call()
        decimals = t.decimals().call()
        tree_balance = t.balanceOf(ETH_BADGER_TREE).call() / (10 ** int(decimals))
        total = float(snap.total_balance())
        deficit[name] = tree_balance - total
        logger.info(name)
        logger.info("Tree Balance: {}".format(tree_balance))
        logger.info("Claimable Balance: {}".format(total))
        logger.info("Deficit: {}".format(tree_balance - total))
        logger.info("\n")

    print(json.dumps(deficit, indent=4, sort_keys=True))
