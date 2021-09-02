from helpers.discord import send_message_to_discord
from subgraph.subgraph_utils import make_gql_client
from rich.console import Console
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from decimal import *
import math
from functools import lru_cache
from config.env_config import env_config
import json

getcontext().prec = 20
console = Console()

tokens_client = make_gql_client("tokens")
harvests_client = make_gql_client("harvests")

## TODO: seperate files by chain/subgraph


def fetch_tree_distributions(startBlock, endBlock):
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
        results = harvests_client.execute(query, variable_values=variables)
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


@lru_cache(maxsize=None)
def fetch_token_balances(client, sharesPerFragment, blockNumber):
    increment = 1000
    query = gql(
        """
        query fetchWalletBalance($firstAmount: Int, $lastID: ID, $blockNumber:Block_height) {
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
    try:
        while continueFetching:
            variables = {
                "firstAmount": increment,
                "lastID": lastID,
                "blockNumber": {"number": blockNumber - 50},
            }
            nextPage = client.execute(query, variable_values=variables)
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
    except Exception as e:
        send_message_to_discord(
            "**BADGER BOOST ERROR**",
            f":x: Error in Fetching Token Balance",
            [
                {
                    "name": "Error Type",
                    "value": type(e),
                    "inline": True,
                    "name": "Error Description",
                    "value": e.args,
                    "inline": True,
                }
            ],
            "Boost Bot",
        )
        raise e

    return badger_balances, digg_balances


def fetch_chain_balances(chain, block):
    client = make_gql_client(chain)
    query = gql(
        """
        query balances($blockHeight: Block_height,$lastId:UserSettBalance_filter) {
            userSettBalances(first: 1000, block: $blockHeight, where:$lastId) {
                id
                user {
                    id
                }
                sett {
                    id
                    token{
                        decimals
                    }
                }
                netShareDeposit
            }
        }
        """
    )
    lastId = ""
    variables = {"blockHeight": {"number": block - 50}}
    balances = {}
    try:
        while True:
            variables["lastId"] = {"id_gt": lastId}
            results = client.execute(query, variable_values=variables)
            balanceData = results["userSettBalances"]
            for result in balanceData:
                account = result["user"]["id"].lower()
                decimals = int(result["sett"]["token"]["decimals"])
                sett = result["sett"]["id"]
                if sett == "0x7e7E112A68d8D2E221E11047a72fFC1065c38e1a".lower():
                    decimals = 18
                deposit = float(result["netShareDeposit"]) / math.pow(10, decimals)
                if deposit > 0:
                    if sett not in balances:
                        balances[sett] = {}

                    if account not in balances[sett]:
                        balances[sett][account] = deposit
                    else:
                        balances[sett][account] += deposit

            if len(balanceData) == 0:
                break
            else:
                console.log("Fetching {} sett balances".format(len(balanceData)))
                lastId = balanceData[-1]["id"]
        console.log("Fetched {} total sett balances".format(len(balances)))
        return balances
    except Exception as e:
        send_message_to_discord(
            "**BADGER BOOST ERROR**",
            f":x: Error in Fetching Token Balance",
            [
                {
                    "name": "Error Type",
                    "value": type(e),
                    "inline": True,
                    "name": "Error Description",
                    "value": e.args,
                    "inline": True,
                }
            ],
            "Boost Bot",
        )
        raise e


def fetch_fuse_pool_balances(client, chain, block):
    if chain is not "eth":
        console.log("Fuse pools are only active on ETH")
        return None

    ctoken_data = {
        "fBDIGG-22": {
            "underlying_contract": "0x7e7e112a68d8d2e221e11047a72ffc1065c38e1a",
            "symbol": "fBDIGG-22",
            "contract": "0x4b789c1a3124e9c7945e24d20a5034a85ffb7535",
        },
        "fBBADGER-22": {
            "underlying_contract": "0x19d97d8fa813ee2f51ad4b4e04ea08baf4dffc28",
            "symbol": "fBBADGER-22",
            "contract": "0x8c2ab59d5a0cff6b1d00ef7dd70d85db88483671",
        },
        "fBADGER-22": {
            "underlying_contract": "0x3472A5A71965499acd81997a54BBA8D852C6E53d",
            "symbol": "fBADGER-22",
            "contract": "0x6780B4681aa8efE530d075897B3a4ff6cA5ed807",
        },
    }

    with open("abis/eth/CErc20Delegator.json") as f:
        DELEGATOR_ABI = json.load(f)
    with open("abis/eth/ERC20.json") as j:
        ERC20_ABI = json.load(j)

    for symbol, data in ctoken_data:
        ftoken_contract = env_config.web3.eth.contract(
            address=env_config.web3.toChecksumAddress(data["contract"]),
            abi=DELEGATOR_ABI,
        )
        underlying_contract = env_config.web3.eth.contract(
            address=env_config.web3.toChecksumAddress(data["underlying_contract"]),
            abi=ERC20_ABI,
        )
        ctoken_data[symbol]["decimals"] = int(
            ftoken_contract.functions.decimals().call()
        )
        underlying_decimals = int(underlying_contract.functions.decimals().call())
        mantissa = 18 + underlying_decimals - ctoken_data[symbol]["decimals"]
        ctoken_data[symbol]["exchange_rate"] = float(
            ftoken_contract.functions.exchangeRateStored().call()
        ) / math.pow(10, mantissa)

    query = gql(
        f"""
        query fetch_fuse_pool_balances($skip_amount: Int, $block_number: Block_height) {{
            accountCTokens(block: $block_number, skip: $skip_amount, first: 1000, where: {{ symbol_in:{list(ctoken_data.keys())} }}) {{
                symbol
                account{{
                    id
                }}
                cTokenBalance
            }}
        }}
        """
    )

    skip = 0
    balances = {}

    variables = {"block_number": {"number": block - 50}, "skip_amount": skip}

    try:
        while True:
            variables["skip_amount"] = skip
            results = client.execute(query, variable_values=variables)
            for result in results:
                symbol = result["symbol"]
                ctoken_balance = float(result["cTokenBalance"])
                balance = ctoken_balance * ctoken_data[symbol]["exchange_rate"]
                account = result["account"]["id"].lower()

                if balance <= 0:
                    continue

                sett = ctoken_data[symbol]["underlying_contract"]

                if sett not in balances:
                    balances[sett] = {}

                    if account not in balances[sett]:
                        balances[sett][account] = balance
                    else:
                        balances[sett][account] += balance

            if len(results) == 0:
                break
            else:
                console.log("Fetching {} fuse balances".format(len(results)))
                skip += 1000

        console.log("Fetched {} total fuse balances".format(len(balances)))
        return balances

    except Exception as e:
        send_message_to_discord(
            "**BADGER BOOST ERROR**",
            f":x: Error in Fetching Token Balance",
            [
                {
                    "name": "Error Type",
                    "value": type(e),
                    "inline": True,
                    "name": "Error Description",
                    "value": e.args,
                    "inline": True,
                }
            ],
            "Boost Bot",
        )
        raise e
