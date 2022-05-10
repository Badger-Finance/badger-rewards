from collections import Counter
from decimal import Decimal
from typing import Dict
from typing import List

from rich.console import Console
from config.constants import addresses
from helpers.enums import Abi
from helpers.enums import Network
from helpers.web3_utils import make_contract
from rewards.classes.Boost import BoostBalances
from rewards.classes.Snapshot import Snapshot
from rewards.snapshot.chain_snapshot import chain_snapshot_usd
from rewards.snapshot.chain_snapshot import sett_snapshot
from rewards.snapshot.claims_snapshot import claims_snapshot
from rewards.snapshot.claims_snapshot import claims_snapshot_usd
from rewards.snapshot.nft_snapshot import nft_snapshot_usd
from rewards.snapshot.token_snapshot import token_snapshot_usd, fuse_snapshot_of_token
from rewards.utils.snapshot_utils import digg_snapshot_usd

console = Console()


def get_bvecvx_lp_ratio() -> Decimal:
    bvecvx_pool = make_contract(addresses.BVECVX_CVX_LP, Abi.Stableswap, Network.Ethereum)
    balances = bvecvx_pool.get_balances().call()
    return Decimal(balances[1] / sum(balances))  # [cvx, bvecvx]


def get_bvecvx_lp_ppfs() -> Decimal:
    bvecvx_lp = make_contract(addresses.BVECVX_CVX_LP_SETT, Abi.Vault, Network.Ethereum)
    price_per_full_share = bvecvx_lp.getPricePerFullShare().call()
    return Decimal(price_per_full_share / 1e18)


def calc_union_addresses(
        native_setts: Dict[str, float], non_native_setts: Dict[str, float]
) -> List[str]:
    """
    Combine addresses from native setts and non native setts
    :param native_setts: native setts
    :param non_native_setts: non native setts
    """
    native_addresses = list(native_setts.keys())
    non_native_addresses = list(non_native_setts.keys())
    return list(set(native_addresses + non_native_addresses))


def filter_dust(balances: Dict[str, float], dust_amount: int) -> Dict[str, float]:
    """
    Filter out dust values from user balances
    :param balances: balances to filter
    :param dust_amount: dollar amount to filter by
    """
    return {addr: value for addr, value in balances.items() if value > dust_amount}


def calc_boost_balances(block: int, chain: str) -> BoostBalances:
    """
    Calculate boost data required for boost calculation
    :param block: block to collect the boost data from
    :param chain: target chain
    """

    native = Counter()
    non_native = Counter()

    console.log(f"\n === Taking nft snapshot on {chain} === \n")
    nft_balances = nft_snapshot_usd(chain, block)
    console.log(f"\n === Taking claims snapshot on {chain} === \n")
    native_claimable, non_native_claimable = claims_snapshot_usd(chain, block)
    native += Counter(native_claimable)
    non_native += Counter(non_native_claimable)

    console.log(f"\n === Taking token snapshot on {chain} === \n")
    badger_tokens, digg_tokens = token_snapshot_usd(chain, block)

    native += Counter(badger_tokens) + Counter(nft_balances)

    console.log(f"\n === Taking chain snapshot on {chain} === \n")
    native_setts, non_native_setts = chain_snapshot_usd(chain, block)
    non_native += Counter(non_native_setts)
    native += Counter(native_setts)

    bvecvx_usd = {}
    digg_usd = {}
    digg_claimable = Snapshot(addresses.DIGG, {})
    bvecvx_claimable = Snapshot(addresses.BVECVX, {})
    if chain == Network.Ethereum:
        all_claims = claims_snapshot(chain, block)
        bvecvx_claimable = all_claims.get(addresses.BVECVX, bvecvx_claimable)
        digg_claimable = all_claims.get(addresses.DIGG, digg_claimable)
        bvecvx_bals = sett_snapshot(chain, block, addresses.BVECVX)
        fuse_bvecvx = fuse_snapshot_of_token(chain, block, token=addresses.BVECVX)
        bvecvx_lp_bals = sett_snapshot(chain, block, addresses.BVECVX_CVX_LP_SETT)
        ratio = get_bvecvx_lp_ratio()
        ppfs = get_bvecvx_lp_ppfs()
        for addr, value in bvecvx_lp_bals:
            bvecvx_lp_bals.boost_balance(addr, ratio)
            bvecvx_lp_bals.boost_balance(addr, ppfs)
        bvecvx = (bvecvx_bals + bvecvx_claimable + bvecvx_lp_bals + fuse_bvecvx)
        bvecvx_usd = bvecvx.convert_to_usd(chain).balances

    digg_claimable_usd = Counter(digg_claimable.convert_to_usd(chain).balances)
    digg_usd = digg_claimable_usd + Counter(digg_tokens) + Counter(digg_snapshot_usd(chain, block))

    native = filter_dust(dict(native), 1)
    non_native = filter_dust(dict(non_native), 1)
    bvecvx_usd = filter_dust(dict(bvecvx_usd), 1)
    digg_usd = filter_dust(dict(bvecvx_usd), 1)

    return BoostBalances(native, non_native, bvecvx_usd, nft_balances, digg_usd)
