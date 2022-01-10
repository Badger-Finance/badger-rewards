import math
from collections import Counter
from functools import lru_cache
from typing import Dict, Tuple

from badger_api.claimable import get_claimable_data
from badger_api.requests import fetch_token_decimals
from helpers.constants import CLAIMABLE_TOKENS, DIGG
from helpers.digg_utils import digg_utils
from helpers.enums import BalanceType, Network
from helpers.web3_utils import make_token
from rewards.classes.Snapshot import Snapshot


@lru_cache
def claims_snapshot(chain: Network, block: int) -> Dict[str, Snapshot]:
    all_claims = get_claimable_data(chain, block)
    chain_claimable_tokens = CLAIMABLE_TOKENS[chain]
    native_tokens = chain_claimable_tokens[BalanceType.Native]
    non_native_tokens = chain_claimable_tokens[BalanceType.NonNative]
    claims_by_token = {}
    snapshots = {}

    for user_claim_snapshot in all_claims:
        address = user_claim_snapshot["address"]
        claimable_balances = user_claim_snapshot["claimableBalances"]
        for claimable_bal in claimable_balances:
            token = claimable_bal["address"]
            token_decimals = fetch_token_decimals(chain, token)
            balance = int(claimable_bal["balance"])
            if token == DIGG:
                balance = digg_utils.shares_to_fragments(balance) / math.pow(
                    10, token_decimals
                )
            else:
                balance = balance / math.pow(10, token_decimals)

            if token not in claims_by_token:
                claims_by_token[token] = {}
            claims_by_token[token][address] = balance

    for token, claims in claims_by_token.items():
        if token in native_tokens:
            token_type = BalanceType.Native
        elif token in non_native_tokens:
            token_type = BalanceType.NonNative
        else:
            token_type = BalanceType.Excluded
        snapshots[token] = Snapshot(token, claims, ratio=1, type=token_type)
    return snapshots


def claims_snapshot_usd(chain: Network, block: int) -> Tuple[Counter, Counter]:
    """Take a snapshot of native and non native claims in usd"""
    snapshot = claims_snapshot(chain, block)
    native = Counter()
    non_native = Counter()
    for sett, claims in snapshot.items():
        usd_claims = claims.convert_to_usd(chain)
        if usd_claims.type == BalanceType.Native:
            native += Counter(usd_claims.balances)
        elif usd_claims.type == BalanceType.NonNative:
            non_native += Counter(usd_claims.balances)

    return native, non_native
