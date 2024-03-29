from collections import Counter
from typing import Dict
from typing import Tuple

from web3 import Web3

from badger_api.requests import fetch_token
from config.constants.emissions import DISABLED_VAULTS
from config.constants.emissions import NATIVE
from config.constants.emissions import NO_BOOST_CHAINS
from config.constants.emissions import NO_BOOST_VAULTS
from helpers.enums import BalanceType
from helpers.enums import Network
from logging_utils import logger
from rewards.classes.Snapshot import Snapshot
from rewards.utils.emission_utils import fetch_unboosted_vaults
from rewards.utils.emission_utils import get_token_weight
from subgraph.queries.setts import fetch_chain_balances
from subgraph.queries.setts import fetch_sett_balances


def chain_snapshot(chain: Network, block: int) -> Dict[str, Snapshot]:
    """
    Take a snapshot of a chains sett balances at a certain block
    :param chain: chain to query
    :param block: block at which to query

    """
    chain_balances = fetch_chain_balances(chain, block)
    balances_by_sett = {}

    for sett_addr, balances in list(chain_balances.items()):
        sett_addr = Web3.toChecksumAddress(sett_addr)
        sett_balances = parse_sett_balances(sett_addr, balances, chain)
        token = fetch_token(chain, sett_addr)
        name = token.get("name", "")
        logger.info(f"Fetched {len(balances)} balances for sett {name}")
        balances_by_sett[sett_addr] = sett_balances

    return balances_by_sett


def total_twap_sett_snapshot(
        chain: Network, start_block: int, end_block: int,
        sett: str, num_historical_snapshots: int,
) -> Snapshot:
    """
    Get a snapshot for total period.
    That should sum up all Snapshots balances
        for the num_historical_snapshots + snapshot at end_block
    """
    assert end_block >= start_block
    snapshot = sett_snapshot(chain, end_block, sett)
    if end_block == start_block or num_historical_snapshots == 0:
        return snapshot
    snapshot += sett_snapshot(chain, start_block, sett)
    rate = int((end_block - start_block) / num_historical_snapshots)
    # If rate == 0 it means that number of snapshots is too big, and it cannot be calculated
    # properly.
    # For ex: start block = 100, end block = 110 and num of snaps = 14,
    # requesting more snapshots than blocks in the timeframe
    if rate == 0:
        return snapshot
    current_block = start_block
    for i in range(num_historical_snapshots - 1):
        current_block += rate
        snapshot += sett_snapshot(chain, current_block, sett)

    return snapshot


def sett_snapshot(chain: Network, block: int, sett: str) -> Snapshot:
    """
    Take a snapshot of a sett on a chain at a certain block
    :param chain:
    :param block:
    :param sett:
    """
    token = fetch_token(chain, sett)
    name = token.get("name", "")
    logger.info(f"Taking snapshot on {chain} of {name} ({sett}) at {block}\n")
    sett_balances = fetch_sett_balances(chain, block, sett)
    return parse_sett_balances(sett, sett_balances, chain)


def parse_sett_balances(
    sett_address: str,
    balances: Dict[str, float],
    chain: Network,
) -> Snapshot:
    """
    Add metadata for boost
    :param sett_address: target sett address
    :param balances: balances of users:
    :param chain: chain where balances come from
    """
    sett_type = BalanceType.Native if sett_address in NATIVE else BalanceType.NonNative
    if chain in NO_BOOST_CHAINS:
        sett_ratio = 1
    else:
        sett_ratio = get_token_weight(sett_address, chain)

    logger.info(f"Sett {sett_address} has type {sett_type} and ratio {sett_ratio} \n")

    return Snapshot(sett_address, balances, sett_ratio, sett_type)


def chain_snapshot_usd(chain: Network, block: int) -> Tuple[Counter, Counter]:
    """Take a snapshot of a chains native/non native balances in usd"""
    total_snapshot = chain_snapshot(chain, block)
    native = Counter()
    non_native = Counter()
    no_boost = DISABLED_VAULTS + fetch_unboosted_vaults(chain, block) + NO_BOOST_VAULTS
    for sett, snapshot in total_snapshot.items():
        if sett in no_boost:
            logger.info(f"{sett} is disabled")
            continue
        usd_snapshot = snapshot.convert_to_usd(chain)
        balances = Counter(usd_snapshot.balances)
        if usd_snapshot.type == BalanceType.Native:
            native += balances
        elif usd_snapshot.type == BalanceType.NonNative:
            non_native += balances

    return native, non_native
