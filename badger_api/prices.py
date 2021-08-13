import requests
from badger_api.config import urls


def fetch_ppfs():
    """
    Fetch ppfs for bbadger and bdigg
    """
    response = requests.get("{}/setts".format(urls["staging"])).json()
    badger = [s for s in response if s["asset"] == "BADGER"][0]
    digg = [s for s in response if s["asset"] == "DIGG"][0]
    return badger["ppfs"], digg["ppfs"]


def fetch_token_prices():
    """
    Fetch token prices for lp tokens
    """
    chains = ["eth", "bsc"]
    prices = {}
    for chain in chains:
        chain_prices = requests.get(
            "{}/prices?chain={}".format(urls["staging"], chain)
        ).json()
        prices = {**prices, **chain_prices}

    return prices
