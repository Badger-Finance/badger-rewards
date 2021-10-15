from badger_api.account import fetch_all_claimable_balances
from rewards.classes.Snapshot import Snapshot
from helpers.constants import BADGER, DIGG, BCVX, BCVXCRV, ARB_BADGER, POLY_BADGER
from typing import Dict, Tuple
from helpers.digg_utils import digg_utils
from helpers.constants import CLAIMABLE_TOKENS
from functools import lru_cache
from collections import Counter


@lru_cache(maxsize=None)
def claims_snapshot(chain: str) -> Dict[str, Snapshot]:
    all_claims = fetch_all_claimable_balances(chain)
    chain_claimable_tokens = CLAIMABLE_TOKENS[chain]
    native_tokens = chain_claimable_tokens["native"]
    non_native_tokens = chain_claimable_tokens["non_native"]
    claims_data = {}
    snapshots = {}
    for addr, claims in all_claims.items():
        for claim in claims:
            token = claim["address"]
            balance = int(claim["balance"])
            if token in chain_claimable_tokens:
                if token == DIGG:
                    balance = digg_utils.shares_to_fragments(balance)
                if token not in claims_data:
                    claims_data[token] = {}
                claims_data[token][addr] = balance

    for token, snapshot in claims_data.items():
        if token in native_tokens:
            snapshots[token] = Snapshot(token, snapshot, ratio=1, type="native")
        if token in non_native_tokens:
            snapshots[token] = Snapshot(token, snapshot, ratio=1, type="nonNative")

    return snapshots


def claims_snapshot_usd(chain: str) -> Tuple[Counter, Counter]:
    """Take a snapshot of native and non native claims in usd"""
    snapshot = claims_snapshot(chain)
    native = Counter()
    non_native = Counter()
    for sett, claims in snapshot.items():
        usd_claims = claims.convert_to_usd()
        balances = Counter(claims.balances)
        if usd_claims.type == "native":
            native = native + balances
        elif usd_claims.type == "nonNative":
            non_native = non_native + balances

    return native, non_native
