from gql import gql
from graphql.language.ast import DocumentNode
from subgraph.subgraph_utils import make_gql_client
from rich.console import Console
from typing import List, Dict
from helpers.discord import send_error_to_discord
from helpers.constants import MAIN_SUBGRAPH_IDS
import math

console = Console()
thegraph_client = make_gql_client("thegraph")


def last_synced_block(chain):
    query = gql(
        f"""
        query last_block {{
            indexingStatuses(subgraphs: ["{MAIN_SUBGRAPH_IDS[chain]}"]) {{
                chains {{
                    latestBlock {{
                        number
                    }}
                }}
            }}
        }}
    """
    )
    result = thegraph_client.execute(query)
    return int(result["indexingStatuses"][0]["chains"][0]["latestBlock"]["number"])


def balances_query() -> DocumentNode:
    """
    Return a graphql query for fetching setts information
    """
    return gql(
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


def list_setts(chain: str) -> List[str]:
    """
    List all setts from a particular chain
    :param chain:
    """
    client = make_gql_client(chain)
    query = gql(
        """
    {
	    setts(first:100) {
            id
            name
        }
    }
    """
    )
    results = client.execute(query)
    return list(map(lambda s: s["id"], results["setts"]))


def fetch_chain_balances(chain: str, block: int) -> Dict[str, Dict[str, int]]:
    """Fetch a chains balances at a particular block

    :param chain:
    :param block:
    """
    client = make_gql_client(chain)
    query = balances_query()
    lastId = ""
    variables = {"blockHeight": {"number": block}}
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
        console.log("Fetched {} total setts".format(len(balances)))
        return balances
    except Exception as e:
        send_error_to_discord(e, "Error in Fetching Sett Balance")
        raise e


def fetch_sett_balances(chain: str, block: int, sett: str):
    """
    Fetch sett balance on a chain at a block
    :param chain:
    :param block:
    :param sett:
    """
    client = make_gql_client(chain)
    query = balances_query()
    lastId = ""
    variables = {
        "blockHeight": {"number": block},
        "lastId": {"id_gt": "", "sett": sett.lower()},
    }
    balances = {}
    try:
        while True:
            variables["lastId"]["id_gt"] = lastId
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
                    if account not in balances:
                        balances[account] = deposit
                    else:
                        balances[account] += deposit

            if len(balanceData) == 0:
                break
            else:
                console.log("Fetching {} sett balances".format(len(balanceData)))
                lastId = balanceData[-1]["id"]

        console.log("Fetched {} total sett balances".format(len(balances)))
        return balances

    except Exception as e:
        send_error_to_discord(e, "Error in Fetching Sett Balance")
        raise e
