import math
from functools import lru_cache
from typing import (
    Dict,
    List,
)

from gql import gql
from graphql.language.ast import DocumentNode
from rich.console import Console
from web3 import Web3

from config.constants.chain_mappings import SETTS
from config.constants.emissions import DIGG_SETTS
from helpers.enums import Network
from subgraph.subgraph_utils import SubgraphClient

console = Console()


@lru_cache
def last_synced_block(chain: Network) -> int:
    """
    Return the last synced block of the setts subgraph of a chain
    """
    chain_client = SubgraphClient(chain, chain)
    query = gql(
        """
        query last_block {
           _meta {
                block {
                    number
                }
            }
        }
        """
    )
    result = chain_client.execute(query)
    return int(result["_meta"]["block"]["number"])


def fetch_deployment_id(chain: Network, name: str) -> str:
    """
    Fetch the deployment id of a subgraph
    """
    client = SubgraphClient(name, chain)
    query = gql(
        """
        {
          _meta{
              deployment
          }
        }
        """
    )
    result = client.execute(query)
    return result["_meta"]["deployment"]


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


def list_setts(chain: Network) -> List[str]:
    """
    List all setts from a particular chain
    :param chain:
    """
    client = SubgraphClient(chain, chain)
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
    return list(map(lambda s: Web3.toChecksumAddress(s["id"]), results["setts"]))


def fetch_chain_balances(chain: Network, block: int) -> Dict[str, Dict[str, int]]:
    """Fetch a chains balances at a particular block

    :param chain:
    :param block:
    """
    client = SubgraphClient(chain, chain)
    query = balances_query()
    last_id = ""
    variables = {"blockHeight": {"number": block}}
    balances = {}
    while True:
        variables["lastId"] = {"id_gt": last_id}
        results = client.execute(query, variable_values=variables)
        balance_data = results["userSettBalances"]
        for result in balance_data:
            account = Web3.toChecksumAddress(result["user"]["id"])
            decimals = int(result["sett"]["token"]["decimals"])
            sett = Web3.toChecksumAddress(result["sett"]["id"])
            if sett in DIGG_SETTS:
                decimals = 18
            deposit = float(result["netShareDeposit"]) / math.pow(10, decimals)
            if deposit > 0:
                if sett not in balances:
                    balances[sett] = {}

                if account not in balances[sett]:
                    balances[sett][account] = deposit
                else:
                    balances[sett][account] += deposit

        if len(balance_data) == 0:
            break
        else:
            console.log(f"Fetching {len(balance_data)} sett balances")
            last_id = balance_data[-1]["id"]
    console.log(f"Fetched {len(balances)} total setts")
    return balances


def fetch_sett_balances(chain: Network, block: int, sett: str):
    """
    Fetch sett balance on a chain at a block
    :param chain:
    :param block:
    :param sett:
    """
    client = SubgraphClient(chain, chain)
    query = balances_query()
    last_id = ""
    variables = {
        "blockHeight": {"number": block},
        "lastId": {"id_gt": "", "sett": sett.lower()},
    }
    balances = {}
    while True:
        variables["lastId"]["id_gt"] = last_id
        results = client.execute(query, variable_values=variables)
        balance_data = results["userSettBalances"]
        for result in balance_data:
            account = Web3.toChecksumAddress(result["user"]["id"])
            decimals = int(result["sett"]["token"]["decimals"])
            sett = Web3.toChecksumAddress(result["sett"]["id"])
            if sett == SETTS[Network.Ethereum]["digg"]:
                decimals = 18
            deposit = float(result["netShareDeposit"]) / math.pow(10, decimals)
            if deposit > 0:
                if account not in balances:
                    balances[account] = deposit
                else:
                    balances[account] += deposit

        if len(balance_data) == 0:
            break
        else:
            console.log(f"Fetching {len(balance_data)} sett balances")
            last_id = balance_data[-1]["id"]

    console.log(f"Fetched {len(balances)} total sett balances")
    return balances
