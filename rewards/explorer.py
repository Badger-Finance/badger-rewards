import requests
from config.env_config import env_config
from typing import Dict
import time

urls = {"polygon": "polygonscan.com", "bsc": "bscscan.com", "arbitrum": "arbiscan.io"}


def get_block_by_timestamp(chain: str, timestamp: int) -> int:

    time.sleep(5)
    chain_url = "https://api.{}".format(urls[chain])
    url = "api?module=block&action=getblocknobytime&timestamp={}&closest=before".format(
        timestamp
    )
    response = requests.get("{}/{}".format(chain_url, url)).json()
    return int(response["result"])


def convert_from_eth(block) -> Dict[str, int]:
    """
    Convert block from eth to blocks on other chains
    """
    timestamp = env_config.get_web3().eth.getBlock(block)["timestamp"]
    return {
        "eth": block,
        # "bsc": get_block_by_timestamp("bsc", timestamp) - 1000,
        "polygon": get_block_by_timestamp("polygon", timestamp) - 1000,
        "arbitrum": get_block_by_timestamp("arbitrum", timestamp) - 1500,
    }


def get_explorer_url(chain: str, txHash: str) -> str:
    return "https://{}/tx/{}".format(urls[chain], txHash)
