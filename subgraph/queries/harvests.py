from gql import gql
from subgraph.subgraph_utils import make_gql_client
from rich.console import Console

console = Console()

harvests_client = make_gql_client("harvests-ethereum")


def fetch_tree_distributions(start_timestamp, end_timestamp, chain):
    tree_client = make_gql_client(f"harvests-{chain}")
    query = gql(
        """
        query tree_distributions(
            $lastDistId: TreeDistribution_filter
            ) {
            treeDistributions(where: $lastDistId) {
                id
                token {
                    address
                    symbol
                }
                amount
                blockNumber
                timestamp
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


def fetch_farm_harvest_events():
    query = gql(
        """
        query fetch_harvest_events {
            farmHarvestEvents(first:1000,orderBy: blockNumber,orderDirection:asc) {
                id
                farmToRewards
                blockNumber
                totalFarmHarvested
                timestamp
            }
        }

    """
    )
    results = harvests_client.execute(query)
    for event in results["farmHarvestEvents"]:
        event["rewardAmount"] = event.pop("farmToRewards")

    return results["farmHarvestEvents"]


def fetch_sushi_harvest_events(start_block, end_block):
    query = gql(
        """
        query fetch_harvest_events {
            sushiHarvestEvents(first:1000,orderBy:blockNumber,orderDirection:asc) {
                id
                xSushiHarvested
                totalxSushi
                toStrategist
                toBadgerTree
                toGovernance
                timestamp
                blockNumber
            }
        }
    """
    )
    results = harvests_client.execute(query)
    wbtc_eth_events = []
    wbtc_badger_events = []
    wbtc_digg_events = []
    ibbtc_wbtc_events = []
    for event in results["sushiHarvestEvents"]:
        event["rewardAmount"] = event.pop("toBadgerTree")
        strategy = event["id"].split("-")[0]
        block_number = int(event["blockNumber"])
        if block_number > start_block and block_number < end_block:
            if strategy == "0x7a56d65254705b4def63c68488c0182968c452ce":
                wbtc_eth_events.append(event)
            elif strategy == "0x3a494d79aa78118795daad8aeff5825c6c8df7f1":
                wbtc_badger_events.append(event)
            elif strategy == "0xaa8dddfe7dfa3c3269f1910d89e4413dd006d08a":
                wbtc_digg_events.append(event)
            elif strategy == "0xf4146a176b09c664978e03d28d07db4431525dad":
                ibbtc_wbtc_events.append(event)

    return {
        "0x7a56d65254705b4def63c68488c0182968c452ce": wbtc_eth_events,
        "0x3a494d79aa78118795daad8aeff5825c6c8df7f1": wbtc_badger_events,
        "0xaa8dddfe7dfa3c3269f1910d89e4413dd006d08a": wbtc_digg_events,
        "0xf4146a176b09c664978e03d28d07db4431525dad": ibbtc_wbtc_events,
    }
