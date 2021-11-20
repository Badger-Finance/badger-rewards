import time
from typing import Dict, List, Optional, Union

from config.singletons import env_config
from helpers.enums import Network
from helpers.http_client import http_client

urls = {
    Network.Ethereum: "etherscan.io",
    Network.Polygon: "polygonscan.com",
    Network.Arbitrum: "arbiscan.io",
}


def fetch_block_by_timestamp(chain: str, timestamp: int) -> Optional[Union[Dict, List]]:
    chain_url = f"https://api.{urls[chain]}"
    url = (
        f"api?module=block&action=getblocknobytime&timestamp={timestamp}&closest=before"
    )
    api_key = f"apikey={env_config.get_explorer_api_key(chain)}"
    return http_client.get(f"{chain_url}/{url}&{api_key}")


def get_block_by_timestamp(chain: str, timestamp: int) -> int:
    response = fetch_block_by_timestamp(chain, timestamp)
    while response["status"] == "0":
        time.sleep(1)
        # API Rate limit is 5 per second
        response = fetch_block_by_timestamp(chain, timestamp)

    return int(response["result"])


def convert_from_eth(block) -> Dict[str, int]:
    """
    Convert block from eth to blocks on other chains
    """
    timestamp = env_config.get_web3().eth.get_block(block)["timestamp"]
    return {
        Network.Ethereum: block,
        Network.Polygon: get_block_by_timestamp(Network.Polygon, timestamp) - 1000,
        Network.Arbitrum: get_block_by_timestamp(Network.Arbitrum, timestamp) - 1500,
    }


def get_explorer_url(chain: str, tx_hash: str) -> str:
    return f"https://{urls[chain]}/tx/{tx_hash}"
