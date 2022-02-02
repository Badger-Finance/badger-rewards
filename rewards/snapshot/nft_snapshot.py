from decimal import Decimal, DecimalException
from typing import Dict

from helpers.constants import BADGER
from helpers.enums import BalanceType, Network
from rewards.classes.Snapshot import Snapshot
from rewards.utils.emission_utils import get_nft_weight
from subgraph.queries.nfts import fetch_nfts


def nft_snapshot(chain: Network, block: int) -> Snapshot:
    nfts = fetch_nfts(chain, block)
    bals = {}
    for user, nft_balances in nfts.items():
        for nft_balance in nft_balances:
            nft_address = nft_balance["address"]
            nft_id = nft_balance["id"]
            bals[user] = bals.get(user, 0) + get_nft_weight(chain, nft_address, nft_id)
    return Snapshot(BADGER, bals, ratio=1, type=BalanceType.Native)


def nft_snapshot_usd(chain: Network, block: int) -> Dict[str, Decimal]:
    return nft_snapshot(chain, block).convert_to_usd(chain).balances
