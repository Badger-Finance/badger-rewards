from subgraph.client import fetch_token_balances
from subgraph.subgraph_utils import make_gql_client
from helpers.digg_utils import diggUtils
from helpers.constants import BADGER, DIGG
from badger_api.prices import fetch_token_prices

prices = fetch_token_prices()

def token_snapshot(chain: str, block: int):
    token_client = make_gql_client("tokens-{}".format(
        chain
    ))
    return fetch_token_balances(
        token_client,
        diggUtils.sharesPerFragment,
        block
    )

def token_snapshot_usd(chain: str, block: int):
    badger_balances, digg_balances = token_snapshot(chain,block)
    return convert_tokens_to_usd(badger_balances, digg_balances)


def convert_tokens_to_usd(badger,digg):
    total = {}
    for addr, bal in badger.items():
        total[addr] = bal * prices[BADGER]
    for addr, bal in digg.items():
        total[addr] = bal * prices[DIGG]
    return total


    

