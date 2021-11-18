import math
from collections import Counter
from functools import lru_cache
from typing import Dict, Tuple

from badger_api.requests import fetch_all_claimable_balances
from helpers.constants import CLAIMABLE_TOKENS, DIGG
from helpers.digg_utils import digg_utils
from helpers.enums import BalanceType
from helpers.web3_utils import make_token
from rewards.classes.Snapshot import Snapshot


def claims_snapshot(chain: str) -> Dict[str, Snapshot]:
    all_claims = fetch_all_claimable_balances(chain)
    chain_claimable_tokens = CLAIMABLE_TOKENS[chain]
    native_tokens = chain_claimable_tokens[BalanceType.Native]
    non_native_tokens = chain_claimable_tokens[BalanceType.NonNative]
    claims_data = {}
    snapshots = {}
    token_decimals = {}
    for addr, claims in all_claims.items():
        for claim in claims:
            token = claim["address"]
            if token not in token_decimals:
                token_contract = make_token(token, chain)
                decimals = token_contract.decimals().call()
                token_decimals[token] = decimals

            balance = int(claim["balance"])
            if token == DIGG:
                balance = digg_utils.shares_to_fragments(balance) / math.pow(
                    10, token_decimals[token]
                )
            else:
                balance = balance / math.pow(10, token_decimals[token])
            if token not in claims_data:
                claims_data[token] = {}

            claims_data[token][addr] = balance

    for token, snapshot in claims_data.items():
        if token in native_tokens:
            snapshots[token] = Snapshot(
                token, snapshot, ratio=1, type=BalanceType.Native
            )
        elif token in non_native_tokens:
            snapshots[token] = Snapshot(
                token, snapshot, ratio=1, type=BalanceType.NonNative
            )
        else:
            snapshots[token] = Snapshot(
                token, snapshot, ratio=1, type=BalanceType.Excluded
            )

    return snapshots


def claims_snapshot_usd(chain: str) -> Tuple[Counter, Counter]:
    """Take a snapshot of native and non native claims in usd"""
    snapshot = claims_snapshot(chain)
    native = Counter()
    non_native = Counter()
    for sett, claims in snapshot.items():
        usd_claims = claims.convert_to_usd(chain)
        if usd_claims.type == BalanceType.Native:
            native = native + Counter(usd_claims.balances)
        elif usd_claims.type == BalanceType.NonNative:
            non_native = non_native + Counter(usd_claims.balances)

    return native, non_native
