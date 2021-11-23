from typing import Dict

from gql import gql

from helpers.discord import send_error_to_discord
from helpers.enums import Network
from subgraph.subgraph_utils import make_gql_client


def fetch_nfts(chain: str, block: int) -> Dict:
    if chain != Network.Ethereum:
        return {}
    
    last_nft_id = ""
    nft_client = make_gql_client("nfts")
    query = gql(
    """
    query nfts($block_number: Block_height, $nft_filter: NFTBalance_filter) {
        nfts(block: $block_number, where: $nft_filter) {
            id
        }
    }
    """
    )
    nft_balances = {}
    variables =  {
        "block_number": {"number": block},
        "nft_filter": {"id_gt": last_nft_id, "amount_gt": 0}
    }
    try:
        while True:
            variables["nft_filter"]["id_gt"] = last_nft_id
            results = nft_client.execute(query, variable_values=variables)
            nft_data = results["nfts"]
            for result in nft_data:
                nft_addr,nft_id, user  = result.split("-")
                nft_balances[user] = nft_balances.get(user, []).append({
                    "address": nft_addr,
                    "id": nft_id
                })
            if len(nft_data) == 0:
                break
            else:
                last_nft_id = nft_data[-1]["id"]
        return nft_balances
    except Exception as e:
        send_error_to_discord(
            e, "Error in Fetching Nfts", "Subgraph Error", chain
        )
        raise e
        
            
    
    
        