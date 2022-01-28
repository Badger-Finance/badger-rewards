from decimal import Decimal
from typing import Dict

from badger_api.requests import fetch_token
from helpers.constants import DIGG
from helpers.digg_utils import digg_utils
from helpers.enums import Network


def totals_info(totals: Dict[str, Decimal], chain: Network) -> str:
    info = []
    for token, amount in totals.items():
        token_info = fetch_token(chain, token)
        name = token_info.get("name", "")
        decimals = token_info.get("decimals", 18)
        if token == DIGG:
            amount = digg_utils.shares_to_fragments(amount)

        info.append(f"{name}: {round(amount/pow(10,decimals), 5)}")
    return "\n".join(info)