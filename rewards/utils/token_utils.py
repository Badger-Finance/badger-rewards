from decimal import Decimal

from badger_api.requests import fetch_token
from helpers.constants import DIGG
from helpers.digg_utils import digg_utils
from helpers.enums import Network


def token_amount_base_10(chain: Network, token: str, amount: Decimal) -> str:
    token_info = fetch_token(chain, token)
    decimals = token_info.get("decimals", 18)
    if token == DIGG:
        amount = digg_utils.shares_to_fragments(amount)

    return str(round(amount/pow(10,decimals), 5))
