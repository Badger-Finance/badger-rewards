import math
from functools import lru_cache
from decimal import Decimal
from numbers import Number
from typing import (
    Dict,
    Tuple,
)

from gql import (
    gql,
)
from rich.console import Console
from web3 import Web3
from config.constants.chain_mappings import DECIMAL_MAPPING
from config.constants.emissions import (
    FTOKEN_DECIMALS,
    FUSE_MANTISSA,
    FUSE_TOKEN_BASE,
    FUSE_TOKEN_INFO
)
from helpers.digg_utils import digg_utils
from helpers.enums import (
    Abi,
    Network,
)
from helpers.web3_utils import make_contract
from subgraph.subgraph_utils import SubgraphClient
from rewards.utils.emission_utils import get_across_lp_multiplier

console = Console()


def token_query():
    """
    Graphql query for fetching tokens on a subgraph
    """
    return gql(
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


def fetch_across_balances(block_number: int, chain: Network) -> Dict[str, int]:
    """
    Fetch lp balances from across protocol and convert to badger tokens
    """
    if chain != Network.Ethereum:
        return {}
    increment = 1000
    query = token_query()
    continue_fetching = True
    last_id = "0x0000000000000000000000000000000000000000"
    multiplier = get_across_lp_multiplier()
    console.log(f"Across lp multiplier {multiplier}")
    across_balances = {}
    client = SubgraphClient("across", chain)
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
                f"Fetching {len(next_page['tokenBalances'])} across balances"
            )
            for entry in next_page["tokenBalances"]:
                address = entry["id"].split("-")[1]
                amount = int(entry["balance"])
                if amount > 0:
                    across_balances[address] = multiplier * amount / DECIMAL_MAPPING[chain]
    return across_balances


@lru_cache(maxsize=None)
def fetch_token_balances(
        block_number: int, chain: Network
) -> Tuple[Dict[str, Number], Dict[str, Number]]:
    increment = 1000
    query = token_query()
    client = SubgraphClient(f"tokens-{chain}", chain)

    continue_fetching = True
    last_id = "0x0000000000000000000000000000000000000000"

    badger_balances = {}
    digg_balances = {}
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
                amount = int(entry["balance"])
                if amount > 0:
                    if entry["token"]["symbol"] == "BADGER":
                        badger_balances[address] = amount / DECIMAL_MAPPING[chain]
                    if entry["token"]["symbol"] == "DIGG":
                        fragment_balance = digg_utils.shares_to_fragments(
                            amount
                        )
                        digg_balances[address] = float(fragment_balance) / 1e9
    return badger_balances, digg_balances


def fetch_fuse_pool_token(chain: Network, block: int, token: str) -> Dict[str, Decimal]:

    if chain != Network.Ethereum:
        return {}

    fuse_client = SubgraphClient("fuse", chain)
    if token not in FUSE_TOKEN_INFO:
        return {}
    token_info = FUSE_TOKEN_INFO[token]
    console.log(f"Fetching {token_info['symbol']} token from fuse pool")
    ftoken = make_contract(
        Web3.toChecksumAddress(token_info["contract"]),
        abi_name=Abi.CErc20Delegator,
        chain=chain
    )
    underlying = make_contract(
        Web3.toChecksumAddress(token_info["underlying"]),
        abi_name=Abi.ERC20,
        chain=chain
    )
    decimals = FTOKEN_DECIMALS
    underlying_decimals = int(underlying.decimals().call())
    mantissa = FUSE_MANTISSA + underlying_decimals - decimals
    exchange_rate = float(ftoken.exchangeRateStored().call()) / math.pow(FUSE_TOKEN_BASE, mantissa)
    last_token_id = "0x0000000000000000000000000000000000000000"

    query = gql(
        """
        query fetch_fuse_pool_balances(
            $block_number: Block_height, $token_filter: AccountCToken_filter
            ) {
            accountCTokens(block: $block_number, where: $token_filter) {
                id
                symbol
                account{
                    id
                }
                cTokenBalance
            }
        }
        """
    )

    balances = {}
    variables = {
        "block_number": {"number": block},
        "token_filter": {"id_gt": last_token_id, "symbol": token_info["symbol"]},
    }
    while True:
        variables["token_filter"]["id_gt"] = last_token_id
        results = fuse_client.execute(query, variable_values=variables)
        for result in results["accountCTokens"]:
            last_token_id = result["id"]
            ctoken_balance = float(result["cTokenBalance"])
            balance = ctoken_balance * exchange_rate
            account = Web3.toChecksumAddress(result["account"]["id"])
            if balance <= 0:
                continue
            balances[account] = balances.get(account, 0) + balance
        if len(results["accountCTokens"]) == 0:
            break
        else:
            console.log(f"Fetching {len(results['accountCTokens'])} fuse balances")

    console.log(f"Fetched {len(balances)} total fuse balances")
    return balances
