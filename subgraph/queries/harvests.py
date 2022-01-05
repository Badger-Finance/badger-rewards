from gql import gql
from rich.console import Console
from web3 import Web3

from subgraph.subgraph_utils import make_gql_client

console = Console()


def fetch_tree_distributions(start_timestamp, end_timestamp, chain):
    tree_client = make_gql_client(chain)
    query = gql(
        """
        query tree_distributions(
            $lastDistId: TokenDistribution_filter
            ) {
            badgerTreeDistributions(where: $lastDistId) {
                id
                token {
                    id
                    symbol
                }
                amount
                blockNumber
                timestamp
                sett {
                    id
                }
                }
            }
        """
    )
    last_dist_id = "0x0000000000000000000000000000000000000000"
    variables = {}
    tree_distributions = []
    while True:
        variables["lastDistId"] = {"id_gt": last_dist_id}
        results = tree_client.execute(query, variable_values=variables)
        dist_data = results["treeDistributions"]
        for dist in dist_data:
            dist["token"] = Web3.toChecksumAddress(dist["token"]["id"])
            dist["sett"] = Web3.toChecksumAddress(dist["sett"]["id"])

        if len(dist_data) == 0:
            break
        else:
            tree_distributions = [*tree_distributions, *dist_data]
        if len(dist_data) > 0:
            last_dist_id = dist_data[-1]["id"]
    return [
        td
        for td in tree_distributions
        if start_timestamp < int(td["timestamp"]) <= end_timestamp
    ]
