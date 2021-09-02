from gql import gql
from subgraph.subgraph_utils import make_gql_client
from rich.console import Console
from typing import Dict, Tuple
from helpers.discord import send_error_to_discord, send_message_to_discord
from helpers.digg_utils import digg_utils
from functools import lru_cache

console = Console()


@lru_cache(maxsize=None)
def fetch_token_balances(client, blockNumber) -> Tuple[Dict[str, int], Dict[str, int]]:
    sharesPerFragment = digg_utils.sharesPerFragment
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

    continueFetching = True
    lastID = "0x0000000000000000000000000000000000000000"

    badger_balances = {}
    digg_balances = {}
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
        send_error_to_discord(e, "Error in Fetching Token Balance")
        raise e

    return badger_balances, digg_balances
