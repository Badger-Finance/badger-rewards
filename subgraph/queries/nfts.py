from gql import gql

from helpers.enums import Network
from subgraph.subgraph_utils import make_gql_client


def fetch_nfts(chain) -> Dict:
    nft_client = make_gql_client("nfts")
    if chain != Network.Ethereum:
        return {}
    else:
        return {}
        