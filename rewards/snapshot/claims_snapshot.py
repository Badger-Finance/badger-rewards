from badger_api.account import fetch_all_claimable_balances
from collections import Counter
from helpers.constants import BADGER, DIGG, BCVX, BCVXCRV
from badger_api.prices import fetch_token_prices


def claims_snapshot():
    all_claims = fetch_all_claimable_balances()
    claimable_tokens = [BADGER, DIGG, BCVX, BCVXCRV]
    snapshot = {}
    for addr, claims in all_claims.items():
        for claim in claims:
            token = claim["token"]
            balance = int(claim["balance"])
            if token in claimable_tokens:
                if addr not in snapshot:
                    snapshot[addr] = {}
                snapshot[addr][token] = balance

    return snapshot


def claims_snapshot_usd():
    snapshot = claims_snapshot()
    native_tokens = [BADGER, DIGG]
    non_native_tokens = [BCVX, BCVXCRV]
    native = {}
    non_native = {}
    prices = fetch_token_prices()
    for addr, claims in snapshot.items():
        if addr not in native:
            for token, balance in claims.items():
                usd_amount = prices[token] * balance
                if token in native_tokens:
                    native[addr] = native.get(addr, 0) + usd_amount
                elif token in non_native_tokens:
                    non_native[addr] = non_native.get(addr, 0) + usd_amount

    return native, non_native
