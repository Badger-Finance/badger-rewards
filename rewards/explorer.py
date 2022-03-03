import time
from typing import Dict, List, Optional, Union

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


def fetch_block_by_timestamp_for_ftm(timestamp: int) -> int:
    query = f"""{{
      blocks(where: {{timestamp_lte: {timestamp}}},orderBy:number, orderDirection:desc, first: 1) {{
        timestamp
        number
      }}
    }}"""
    response = http_client.post(
        "https://api.thegraph.com/subgraphs/name/elkfinance/ftm-blocks", json={'query': query}
    )
    return int(response['data']['blocks'][0]['number'])


def get_block_by_timestamp(chain: Network, timestamp: int) -> int:
    if chain == Network.Fantom:
        return fetch_block_by_timestamp_for_ftm(timestamp)
    response = fetch_block_by_timestamp(chain, timestamp)
    while response["status"] == "0":
        time.sleep(1)
        # API Rate limit is 5 per second
        response = fetch_block_by_timestamp(chain, timestamp)

    return int(response["result"])


def get_explorer_url(chain: Network, tx_hash: str) -> str:
    return f"https://{CHAIN_EXPLORER_URLS[chain]}/tx/{tx_hash}"
