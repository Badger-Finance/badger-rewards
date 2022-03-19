import config.constants.addresses as addresses
from helpers.enums import Network
from subgraph.queries.harvests import fetch_tree_distributions
from config.singletons import env_config
import json

migration_blocks = {
    addresses.BCRV_REN_WBTC: 13597269,
    addresses.BCRV_SBTC: 13608086,
    addresses.BCRV_TBTC: 13608100,
    addresses.BCRV_HBTC: 13608117,
    addresses.BCRV_PBTC: 13608127,
    addresses.BCRV_OBTC: 13608160,
    addresses.BCRV_BBTC: 13608175,
    addresses.BCRV_TRICRYPTO_2: 13608197
}

w3 = env_config.get_web3(Network.Ethereum)
harvests = fetch_tree_distributions(
    w3.eth.getBlock(14367400)["timestamp"],
    w3.eth.getBlock(14367500)["timestamp"],
    chain=Network.Ethereum
)
for dist in harvests:
    dist["block"] = migration_blocks[dist["sett"]]
    for key in list(dist.keys()):
        if key not in ["sett", "block", "token", "amount"]:
            del dist[key]

with open("migration_data.json", "w") as fp:
    json.dump(harvests, fp, indent=4)
