import time
from typing import Dict, List, Optional, Union

from config.constants import ARBITRUM_BLOCK_BUFFER
from config.constants import POLYGON_BLOCK_BUFFER
from config.singletons import env_config
from helpers.enums import Network
from helpers.http_client import http_client

CHAIN_EXPLORER_URLS = {
    Network.Ethereum: "etherscan.io",
    Network.Polygon: "polygonscan.com",
    Network.Arbitrum: "arbiscan.io",
}


def fetch_block_by_timestamp(chain: Network, timestamp: int) -> Optional[Union[Dict, List]]:
    chain_url = f"https://api.{CHAIN_EXPLORER_URLS[chain]}"
    url = (
        f"api?module=block&action=getblocknobytime&timestamp={timestamp}&closest=before"
    )
    api_key = f"apikey={env_config.get_explorer_api_key(chain)}"
    return http_client.get(f"{chain_url}/{url}&{api_key}")


def get_block_by_timestamp(chain: Network, timestamp: int) -> int:
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
        Network.Polygon: get_block_by_timestamp(Network.Polygon, timestamp) - POLYGON_BLOCK_BUFFER,
        Network.Arbitrum: get_block_by_timestamp(
            Network.Arbitrum, timestamp) - ARBITRUM_BLOCK_BUFFER,
    }


def get_explorer_url(chain: Network, tx_hash: str) -> str:
    return f"https://{CHAIN_EXPLORER_URLS[chain]}/tx/{tx_hash}"
