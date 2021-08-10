from classes.EnvConfig import env_config

from functools import lru_cache
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from rich.console import Console

console = Console()

subgraph_ids = {}
subgraph_urls = {
    "setts": "https://bgraph-eth.badger.guru/subgraphs/name/swole/setts",
    "setts_tricrypto": "https://bgraph-eth.badger.guru/subgraphs/name/swole/setts_tricrypto2",
    "tokens": "https://bgraph-eth.badger.guru/subgraphs/name/swole/tokens",
    "harvests": "https://bgraph-eth.badger.guru/subgraphs/name/swole/tree-rewards",
    "nfts": "https://bgraph-eth.badger.guru/subgraphs/name/darruma/badger-nfts",
}


def make_gql_client(name):
    url = subgraph_url(name)
    print(url)
    transport = AIOHTTPTransport(url=url)
    return Client(transport=transport, fetch_schema_from_transport=True)

tokens_client = make_gql_client("tokens")
sett_client = make_gql_client("setts")
sett_tricrypto2_client = make_gql_client("setts_tricrypto")
harvests_client = make_gql_client("harvests")

def subgraph_url(name):
    if name in subgraph_ids:
        return "https://gateway.thegraph.com/api/{}/subgraphs/id/{}".format(
            env_config.graph_api_key, subgraph_ids[name]
        )
    elif name in subgraph_urls:
        return subgraph_urls[name]



@lru_cache(maxsize=None)
def fetch_sett_balances(key, settId, startBlock):
    if key == "native.tricrypto2":
        client = sett_tricrypto2_client
    else:
        client = sett_client
    query = gql(
        """
        query balances_and_events($vaultID: Vault_filter, $blockHeight: Block_height,$lastBalanceId:AccountVaultBalance_filter) {
            vaults(block: $blockHeight, where: $vaultID) {
                balances(first:1000,where: $lastBalanceId) {
                    id
                    account {
                        id
                    }
                    shareBalanceRaw
                  }
                }
            }
        """
    )
    lastBalanceId = ""
    variables = {"blockHeight": {"number": startBlock}, "vaultID": {"id": settId}}
    balances = {}
    while True:
        variables["lastBalanceId"] = {"id_gt": lastBalanceId}

        results = client.execute(query, variable_values=variables)
        if len(results["vaults"]) == 0:
            return {}
        newBalances = {}
        balance_data = results["vaults"][0]["balances"]
        for result in balance_data:
            account = result["id"].split("-")[0]
            newBalances[account] = int(result["shareBalanceRaw"])

        if len(balance_data) == 0:
            break

        if len(balance_data) > 0:
            lastBalanceId = balance_data[-1]["id"]

        balances = {**newBalances, **balances}
    console.log("Processing {} balances".format(len(balances)))
    return balances

@lru_cache(maxsize=None)
def fetch_wallet_balances(sharesPerFragment, blockNumber):
    increment = 1000
    query = gql(
        """
        query fetchWalletBalance($firstAmount: Int, $lastID: ID,$blockNumber:Block_height) {
            tokenBalances(first: $firstAmount, where: { id_gt: $lastID  },block: $blockNumber) {
                id
                balance
                token {
                    symbol
                }
            }
        }
    """
    )

    ## Paginate this for more than 1000 balances
    continueFetching = True
    lastID = "0x0000000000000000000000000000000000000000"

    badger_balances = {}
    digg_balances = {}
    ibbtc_balances = {}
    console.log(sharesPerFragment)
    while continueFetching:
        variables = {
            "firstAmount": increment,
            "lastID": lastID,
            "blockNumber": {"number": blockNumber},
        }
        nextPage = tokens_client.execute(query, variable_values=variables)
        if len(nextPage["tokenBalances"]) == 0:
            continueFetching = False
        else:
            lastID = nextPage["tokenBalances"][-1]["id"]
            console.log(
                "Fetching {} token balances".format(len(nextPage["tokenBalances"]))
            )
            for entry in nextPage["tokenBalances"]:
                address = entry["id"].split("-")[0]
                amount = float(entry["balance"])
                if amount > 0:
                    if entry["token"]["symbol"] == "BADGER":
                        badger_balances[address] = amount / 1e18
                    if entry["token"]["symbol"] == "DIGG":
                        # Speed this up
                        if entry["balance"] == 0:
                            fragmentBalance = 0
                        else:
                            fragmentBalance = sharesPerFragment / amount
                        digg_balances[address] = float(fragmentBalance) / 1e9
                    if entry["token"]["symbol"] == "ibBTC":
                        if (
                            address
                            == "0x18d98D452072Ac2EB7b74ce3DB723374360539f1".lower()
                        ):
                            # Ignore sushiswap pool
                            ibbtc_balances[address] = 0
                        else:
                            ibbtc_balances[address] = amount / 1e18

    return badger_balances, digg_balances, ibbtc_balances



@lru_cache(maxsize=None)
def fetch_geyser_events(geyserId, startBlock):
    console.print(
        "[bold green] Fetching Geyser Events {}[/bold green]".format(geyserId)
    )

    query = gql(
        """query($geyserID: Geyser_filter,$blockHeight: Block_height,$lastStakedId: StakedEvent_filter,$lastUnstakedId: UnstakedEvent_filter)
    {
      geysers(where: $geyserID,block: $blockHeight) {
          id
          totalStaked
          stakeEvents(first:1000,where: $lastStakedId) {
              id
              user,
              amount
              timestamp,
              total
          }
          unstakeEvents(first:1000,where: $lastUnstakedId) {
              id
              user,
              amount
              timestamp,
              total
          }
      }
    }
    """
    )

    stakes = []
    unstakes = []
    totalStaked = 0
    lastStakedId = ""
    lastUnstakedId = ""
    variables = {"geyserID": {"id": geyserId}, "blockHeight": {"number": startBlock}}
    while True:
        variables["lastStakedId"] = {"id_gt": lastStakedId}
        variables["lastUnstakedId"] = {"id_gt": lastUnstakedId}
        result = sett_client.execute(query, variable_values=variables)

        if len(result["geysers"]) == 0:
            return {"stakes": [], "unstakes": [], "totalStaked": 0}
        newStakes = result["geysers"][0]["stakeEvents"]
        newUnstakes = result["geysers"][0]["unstakeEvents"]
        if len(newStakes) == 0 and len(newUnstakes) == 0:
            break
        if len(newStakes) > 0:
            lastStakedId = newStakes[-1]["id"]
        if len(newUnstakes) > 0:
            lastUnstakedId = newUnstakes[-1]["id"]

        stakes.extend(newStakes)
        unstakes.extend(newUnstakes)
        totalStaked = result["geysers"][0]["unstakeEvents"]

    console.log("Processing {} stakes".format(len(stakes)))
    console.log("Processing {} unstakes".format(len(unstakes)))
    return {"stakes": stakes, "unstakes": unstakes, "totalStaked": totalStaked}