from gql import gql
from subgraph.subgraph_utils import make_gql_client
from config.env_config import env_config
import math
from rich.console import Console
from typing import Dict, Tuple
from helpers.discord import send_error_to_discord, send_message_to_discord
from helpers.digg_utils import digg_utils
from helpers.web3_utils import make_contract
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


def fetch_fuse_pool_balances(client, chain, block):
    if chain != "eth":
        console.log("Fuse pools are only active on ETH")
        return {}

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
        "fDIGG-22": {
            "underlying_contract": "0x798D1bE841a82a273720CE31c822C61a67a601C3",
            "symbol": "fDIGG-22",
            "contract": "0x792a676dD661E2c182435aaEfC806F1d4abdC486",
        },
    }

    for symbol, data in ctoken_data.items():
        ftoken = make_contract(
            env_config.get_web3().toChecksumAddress(data["contract"]),
            abiName="CErc20Delegator",
            chain=chain,
        )
        underlying = make_contract(
            env_config.get_web3().toChecksumAddress(data["underlying_contract"]),
            abiName="ERC20",
            chain=chain,
        )

        ctoken_data[symbol]["decimals"] = int(ftoken.decimals().call())
        console.log(ctoken_data[symbol]["decimals"])
        underlying_decimals = int(underlying.decimals().call())
        mantissa = 18 + underlying_decimals - ctoken_data[symbol]["decimals"]
        ctoken_data[symbol]["exchange_rate"] = float(
            ftoken.exchangeRateStored().call()
        ) / math.pow(10, mantissa)

    last_token_id = "0x0000000000000000000000000000000000000000"

    query = gql(
        f"""
        query fetch_fuse_pool_balances($block_number: Block_height, $token_filter: AccountCToken_filter) {{
            accountCTokens(block: $block_number, where: $token_filter) {{
                id
                symbol
                account{{
                    id
                }}
                cTokenBalance
            }}
        }}
        """
    )

    balances = {}
    variables = {
        "block_number": {"number": block - 50},
        "token_filter": {"id_gt": last_token_id, "symbol_in": list(ctoken_data.keys())},
    }
    try:
        while True:
            variables["token_filter"]["id_gt"] = last_token_id
            results = client.execute(query, variable_values=variables)

            for result in results["accountCTokens"]:

                print(result)
                last_token_id = result["id"]
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

            if len(results["accountCTokens"]) == 0:
                break
            else:
                console.log("Fetching {} fuse balances".format(len(results)))

        console.log("Fetched {} total fuse balances".format(len(balances)))
        return balances

    except Exception as e:
        send_message_to_discord(
            "**BADGER BOOST ERROR**",
            f":x: Error in Fetching Fuse Token Balance",
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
