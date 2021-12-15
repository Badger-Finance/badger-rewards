import math
from collections import Counter
from functools import lru_cache
from typing import Dict, Tuple

from badger_api.claimable import get_claimable_balances, get_claimable_snapshot
from badger_api.requests import fetch_all_claimable_balances
from helpers.constants import CLAIMABLE_TOKENS, DIGG
from helpers.digg_utils import digg_utils
from helpers.enums import BalanceType
from helpers.web3_utils import make_token
from rewards.classes.Snapshot import Snapshot


@lru_cache
def claims_snapshot(chain: str, block: int) -> Dict[str, Snapshot]:
    snapshot = get_claimable_snapshot(chain, 0, block)

def claims_snapshot_usd(chain: str, block: int) -> Tuple[Counter, Counter]:
    """Take a snapshot of native and non native claims in usd"""
    snapshot = claims_snapshot(chain, block)
    native = Counter()
    non_native = Counter()
    for sett, claims in snapshot.items():
        usd_claims = claims.convert_to_usd(chain)
        if usd_claims.type == BalanceType.Native:
            native = native + Counter(usd_claims.balances)
        elif usd_claims.type == BalanceType.NonNative:
            non_native = non_native + Counter(usd_claims.balances)

    return native, non_native
