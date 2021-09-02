from gql import gql
from subgraph.subgraph_utils import make_gql_client
from rich.console import Console

console = Console()

harvests_client = make_gql_client("harvests-eth")


def fetch_tree_distributions(startBlock, endBlock, chain):
    tree_client = make_gql_client("harvests-{}".format(chain))
    console.log(startBlock, endBlock)
    query = gql(
        """
        query tree_distributions(
            $blockHeight: Block_height
            $lastDistId: TreeDistribution_filter
            ) {
            treeDistributions(block: $blockHeight, where: $lastDistId) {
                id
                token {
                    address
                    symbol
                }
                amount
                blockNumber
                }
            }
        """
    )
    lastDistId = "0x0000000000000000000000000000000000000000"
    variables = {"blockHeight": {"number": endBlock}}
    treeDistributions = []
    while True:
        variables["lastDistId"] = {"id_gt": lastDistId}
        results = tree_client.execute(query, variable_values=variables)
        distData = results["treeDistributions"]
        if len(distData) == 0:
            break
        else:
            treeDistributions = [*treeDistributions, *distData]
        if len(distData) > 0:
            lastDistId = distData[-1]["id"]
    return [td for td in treeDistributions if int(td["blockNumber"]) > int(startBlock)]


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


def fetch_sushi_harvest_events():
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
    wbtcEthEvents = []
    wbtcBadgerEvents = []
    wbtcDiggEvents = []
    iBbtcWbtcEvents = []
    for event in results["sushiHarvestEvents"]:
        event["rewardAmount"] = event.pop("toBadgerTree")
        strategy = event["id"].split("-")[0]
        if strategy == "0x7a56d65254705b4def63c68488c0182968c452ce":
            wbtcEthEvents.append(event)
        elif strategy == "0x3a494d79aa78118795daad8aeff5825c6c8df7f1":
            wbtcBadgerEvents.append(event)
        elif strategy == "0xaa8dddfe7dfa3c3269f1910d89e4413dd006d08a":
            wbtcDiggEvents.append(event)
        elif strategy == "0xf4146a176b09c664978e03d28d07db4431525dad":
            iBbtcWbtcEvents.append(event)

    return {
        "wbtcEth": wbtcEthEvents,
        "wbtcBadger": wbtcBadgerEvents,
        "wbtcDigg": wbtcDiggEvents,
        "iBbtcWbtc": iBbtcWbtcEvents,
    }
