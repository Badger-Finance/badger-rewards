from decimal import Decimal, DecimalException
from typing import Dict

from helpers.constants import BADGER
from helpers.enums import BalanceType, Network
from rewards.classes.Snapshot import Snapshot
from rewards.utils.emission_utils import get_nft_score
from subgraph.queries.nfts import fetch_nfts


def nft_snapshot(chain: Network) -> Snapshot:
    nfts = fetch_nfts(chain)
    bals = {}
    for user, nft_balances in nfts.items():
        for nft_balance in nft_balances:
            nft_address = nft_balance["address"]
            nft_id = nft_balance["id"]
            bals[user] = bals.get(user, 0) + get_nft_score(nft_address, nft_id)
    return Snapshot(BADGER, bals, ratio=1, type=BalanceType.Native)


def nft_snapshot_usd(chain: Network) -> Dict[str, Decimal]:
    return nft_snapshot(chain).convert_to_usd(chain).balances
