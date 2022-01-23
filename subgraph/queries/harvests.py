from collections import defaultdict
from typing import Dict, List

from gql import gql
from rich.console import Console
from web3 import Web3

from subgraph.subgraph_utils import make_gql_client

console = Console()


def _populate_end_of_previous_harvest(tree_distributions: List[Dict]):
    """
    This function groups distributions by sett and adds
    param end_of_previous_dist_timestamp to each distribution item
    """
    grouped_distributions_by_sett = defaultdict(list)
    for distribution in tree_distributions:
        grouped_distributions_by_sett[distribution['sett']].append(distribution)
    for sett, dists in grouped_distributions_by_sett.items():
        grouped_distributions_by_sett[sett] = sorted(dists, key=lambda d: d["timestamp"])
    # For each distribution populate end of the distribution behind it by adding
    # end_of_previous_dist data point. If this is a first distribution returned from subgraph,
    # end_of_previous_dist should be same as start of current distribution
    for __, distributions in grouped_distributions_by_sett.items():
        for dist in distributions:
            if distributions.index(dist) == 0:
                dist['end_of_previous_dist_timestamp'] = dist['timestamp']
                continue
            dist['end_of_previous_dist_timestamp'] = int(
                distributions[distributions.index(dist) - 1]["timestamp"]
            )
    return grouped_distributions_by_sett


def fetch_tree_distributions(start_timestamp, end_timestamp, chain) -> List[Dict]:
    tree_client = make_gql_client(chain)
    query = gql(
        """
        query tree_distributions(
            $lastDistId: BadgerTreeDistribution_filter
            ) {
            badgerTreeDistributions(where: $lastDistId) {
                id
                token {
                    id
                    symbol
                }
                strategy {
                    id
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
        dist_data = results["badgerTreeDistributions"]
        for dist in dist_data:
            # Subgraph sometimes sends token ids as 0x0x123123123 values and
            # that's why it is needed to rstrip 0x once to make token id valid hex string
            if dist["token"]["id"].startswith("0x0x"):
                dist["token"] = Web3.toChecksumAddress(
                    dist["token"]["id"].replace("0x", "", 1)
                )
            else:
                dist["token"] = Web3.toChecksumAddress(dist["token"]["id"])
            dist["sett"] = Web3.toChecksumAddress(dist["sett"]["id"])
            dist["strategy"] = Web3.toChecksumAddress(dist["strategy"]["id"])

        if len(dist_data) == 0:
            break
        else:
            tree_distributions = [*tree_distributions, *dist_data]
        if len(dist_data) > 0:
            last_dist_id = dist_data[-1]["id"]
    modified_tree_distributions = _populate_end_of_previous_harvest(tree_distributions)

    return [
        distr
        for grouped_distrs in modified_tree_distributions.values() for distr in grouped_distrs
        if start_timestamp < int(distr["timestamp"]) <= end_timestamp
    ]
