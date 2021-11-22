from typing import Dict

from helpers.constants import BADGER
from helpers.enums import Network
from rewards.classes.Snapshot import Snapshot
from subgraph.queries.nfts import fetch_nfts


def nft_snapshot(chain: Network) -> Snapshot:
    nfts = fetch_nfts(chain) 
    
    
    
def nft_snapshot_usd(chain: Network) -> Dict[str, float]:
    return nft_snapshot(chain).convert_to_usd(chain).balances
    
