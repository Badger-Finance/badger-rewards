import math
from functools import lru_cache
from typing import Dict, Optional, Tuple

from gql import Client, gql
from rich.console import Console
from web3 import Web3

from helpers.digg_utils import digg_utils
from helpers.discord import (
    get_discord_url,
    send_error_to_discord,
    send_message_to_discord,
)
from helpers.enums import BotType, Network
from helpers.web3_utils import make_contract

console = Console()


@lru_cache(maxsize=None)
def fetch_token_balances(
        client: Client, block_number: int, chain: Optional[str] = "eth"
) -> Tuple[Dict[str, float], Dict[str, float]]:
    shares_per_fragment = digg_utils.shares_per_fragment
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

    continue_fetching = True
    last_id = "0x0000000000000000000000000000000000000000"

    badger_balances = {}
    digg_balances = {}
    try:
        while continue_fetching:
            variables = {
                "firstAmount": increment,
                "lastID": last_id,
                "blockNumber": {"number": block_number},
            }
            next_page = client.execute(query, variable_values=variables)
            if len(next_page["tokenBalances"]) == 0:
                continue_fetching = False
            else:
                last_id = next_page["tokenBalances"][-1]["id"]
                console.log(
                    f"Fetching {len(next_page['tokenBalances'])} token balances"
                )
                for entry in next_page["tokenBalances"]:
                    address = entry["id"].split("-")[0]
                    amount = float(entry["balance"])
                    if amount > 0:
                        if entry["token"]["symbol"] == "BADGER":
                            badger_balances[address] = amount / 1e18
                        if entry["token"]["symbol"] == "DIGG":
                            # Speed this up
                            if entry["balance"] == 0:
                                fragment_balance = 0
                            else:
                                fragment_balance = digg_utils.shares_to_fragments(
                                    int(amount)
                                )
                            digg_balances[address] = float(fragment_balance) / 1e9
    except Exception as e:
        send_error_to_discord(
            e, "Error in Fetching Token Balance", "Subgraph Error", chain
        )
        raise e

    return badger_balances, digg_balances


def fetch_fuse_pool_balances(client, chain, block):
    if chain != Network.Ethereum:
        console.log("Fuse pools are only active on ETH")
        return {}

    ctoken_data = {
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
            Web3.toChecksumAddress(data["contract"]),
            abi_name="CErc20Delegator",
            chain=chain,
        )
        underlying = make_contract(
            Web3.toChecksumAddress(data["underlying_contract"]),
            abi_name="ERC20",
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
        "block_number": {"number": block},
        "token_filter": {"id_gt": last_token_id, "symbol_in": list(ctoken_data.keys())},
    }
    try:
        while True:
            variables["token_filter"]["id_gt"] = last_token_id
            results = client.execute(query, variable_values=variables)

            for result in results["accountCTokens"]:

                last_token_id = result["id"]
                symbol = result["symbol"]
                ctoken_balance = float(result["cTokenBalance"])
                balance = ctoken_balance * ctoken_data[symbol]["exchange_rate"]
                account = Web3.toChecksumAddress(result["account"]["id"])

                if balance <= 0:
                    continue

                sett = Web3.toChecksumAddress(
                    ctoken_data[symbol]["underlying_contract"]
                )

                if sett not in balances:
                    balances[sett] = {}

                if account not in balances[sett]:
                    balances[sett][account] = balance
                else:
                    balances[sett][account] += balance

            if len(results["accountCTokens"]) == 0:
                break
            else:
                console.log(f"Fetching {len(results['accountCTokens'])} fuse balances")

        console.log(f"Fetched {len(balances)} total fuse balances")
        return balances

    except Exception as e:
        discord_url = get_discord_url(chain, BotType.Boost)
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
            url=discord_url,
        )
        raise e
