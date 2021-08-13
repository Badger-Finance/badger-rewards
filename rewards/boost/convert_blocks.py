import requests
from brownie import web3

urls = {"polygon": "https://api.polygonscan.com", "bsc": "https://api.bscscan.com"}


def get_block_by_timestamp(chain: str, timestamp: int):
    url = "api?module=block&action=getblocknobytime&timestamp={}&closest=before".format(
        timestamp
    )
    response = requests.get("{}/{}".format(urls[chain], url)).json()
    return int(response["result"])


def convert_from_eth(block):
    """
    Convert block from eth to blocks on other chains
    """
    timestamp = web3.eth.getBlock(block)["timestamp"]
    return {
        "eth": block,
        "bsc": get_block_by_timestamp("bsc", timestamp) - 1000,
        "polygon": get_block_by_timestamp("polygon", timestamp) - 1000,
    }
