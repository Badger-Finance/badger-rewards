from functools import lru_cache
from typing import Dict

from gql import gql
from web3.main import Web3

from helpers.enums import Network
from logging_utils import logger
from subgraph.subgraph_utils import SubgraphClient


@lru_cache
def fetch_nfts(chain: str, block: int) -> Dict:
    if chain != Network.Ethereum:
        return {}
    last_nft_id = ""
    nft_client = SubgraphClient("nfts", chain)
    query = gql(
        """
    query nfts($block_number: Block_height, $nft_filter: NFTBalance_filter) {
        nftbalances(first: 1000, block: $block_number, where: $nft_filter) {
            id
        }
    }
    """
    )
    nft_balances = {}
    BLOCK_DELAY = 500
    variables = {
        "block_number": {"number": block - BLOCK_DELAY},
        "nft_filter": {"id_gt": last_nft_id, "amount_gt": 0},
    }
    while True:
        variables["nft_filter"]["id_gt"] = last_nft_id
        results = nft_client.execute(query, variable_values=variables)
        nft_data = results["nftbalances"]
        for result in nft_data:
            nft_addr, nft_id, user = result["id"].split("-")
            user = Web3.toChecksumAddress(user)
            if user not in nft_balances:
                nft_balances[user] = []
            nft_balances[user].append(
                {"address": Web3.toChecksumAddress(nft_addr), "id": nft_id}
            )
        if len(nft_data) == 0:
            break
        else:
            logger.info(f"Fetching {len(nft_data)} nft balances")
            last_nft_id = nft_data[-1]["id"]
    return nft_balances
