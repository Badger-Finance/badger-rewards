import requests
from badger_api.config import urls
from typing import Tuple, Dict

def fetch_ppfs() -> Tuple[float, float]:
    """
    Fetch ppfs for bbadger and bdigg
    """
    response = requests.get("{}/setts".format(urls["staging"])).json()
    badger = [s for s in response if s["asset"] == "BADGER"][0]
    digg = [s for s in response if s["asset"] == "DIGG"][0]
    return badger["ppfs"], digg["ppfs"]


def fetch_token_prices() -> Dict[str, float]:
    """
    Fetch token prices for settt tokens
    """
    response = requests.get("{}/prices".format(urls["staging"])).json()
    return response
