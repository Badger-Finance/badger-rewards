import math
from decimal import Decimal

import pytest
import responses
from pytest import approx

from badger_api.requests import badger_api
from config.constants.addresses import (
    ARB_BSWAPR_WETH_SWAPR,
    BADGER,
    BCVXCRV,
    DIGG,
    WBTC,
    POLY_SUSHI,
    XSUSHI,
)
from config.constants.chain_mappings import NETWORK_TO_BADGER_TOKEN
from config.constants.emissions import BOOST_CHAINS
from conftest import MockDiggUtils
from helpers.enums import BalanceType, Network
from rewards.snapshot.claims_snapshot import claims_snapshot, claims_snapshot_usd
from tests.utils import (
    TEST_WALLET,
    TEST_WALLET_ANOTHER,
    CLAIMABLE_BALANCES_DATA_ARB,
    CLAIMABLE_BALANCES_DATA_ETH,
    CLAIMABLE_BALANCES_DATA_POLY,
    mock_get_claimable_data
)
BADGER_PRICE = 27.411460272851376
XSUSHI_PRICE = 1.201460272851376
CVX_CRV_PRICE = 12.411460272851376
SWAPR_WETH_SWAPR_PRICE = 12312.201460272851376
DIGG_PRICE = 50000
WBTC_PRICE = 30000


@pytest.fixture()
def claimable_block():
    return 13952759


@pytest.mark.parametrize(
    "chain, data",
    [
        (Network.Ethereum, CLAIMABLE_BALANCES_DATA_ETH),
        (Network.Polygon, CLAIMABLE_BALANCES_DATA_POLY),
        (Network.Arbitrum, CLAIMABLE_BALANCES_DATA_ARB),
    ],
)
def test_claims_snapshot__happy(
    chain,
    data,
    claimable_block,
    mocker,
    fetch_token_mock,
):
    mocker.patch(
        "rewards.snapshot.claims_snapshot.get_claimable_data", mock_get_claimable_data
    )
    snapshots = claims_snapshot(chain, claimable_block)

    badger_snapshot = snapshots[NETWORK_TO_BADGER_TOKEN[chain]]
    assert badger_snapshot.type == BalanceType.Native
    assert badger_snapshot.ratio == 1
    assert badger_snapshot.token == NETWORK_TO_BADGER_TOKEN[chain]
    expected_badger_balance = 0
    for claim in data["rewards"][TEST_WALLET]:
        if claim["address"] == NETWORK_TO_BADGER_TOKEN[chain]:
            expected_badger_balance = int(claim["balance"]) / math.pow(10, 18)
    assert badger_snapshot.balances[TEST_WALLET] == approx(
        Decimal(expected_badger_balance)
    )

    excluded_token = None
    non_native_token = None
    if chain == Network.Ethereum:
        excluded_token = XSUSHI
        non_native_token = BCVXCRV
    elif chain == Network.Polygon:
        excluded_token = POLY_SUSHI
    elif chain == Network.Arbitrum:
        excluded_token = ARB_BSWAPR_WETH_SWAPR
    for token in [excluded_token, non_native_token]:
        if token:
            snapshot = snapshots[excluded_token]
            assert snapshot.ratio == 1
            expected_token_balance = 0
            for claim in data["rewards"][TEST_WALLET]:
                if claim["address"] == excluded_token:
                    expected_token_balance = int(claim["balance"]) / math.pow(10, 18)
            assert snapshot.balances[TEST_WALLET] == approx(
                Decimal(expected_token_balance)
            )


def test_claims_snapshot_digg(claimable_block, mocker, fetch_token_mock):
    # Digg has different calculation algorithm hence separate test
    balance = "148480869281534217908"
    mocker.patch(
        "rewards.snapshot.claims_snapshot.get_claimable_data", mock_get_claimable_data
    )
    digg_utils = MockDiggUtils()
    snapshots = claims_snapshot(Network.Ethereum, claimable_block)
    digg_snapshot = snapshots[DIGG]
    assert digg_snapshot.type == BalanceType.Excluded
    assert digg_snapshot.ratio == 1
    assert digg_snapshot.token == DIGG
    expected_digg_balance = digg_utils.shares_to_fragments(int(balance)) / math.pow(
        10, 18
    )
    assert digg_snapshot.balances[TEST_WALLET_ANOTHER] == approx(
        Decimal(expected_digg_balance)
    )


@responses.activate
def test_claims_snapshot_usd__happy(claimable_block, mocker, fetch_token_mock):
    mocker.patch(
        "rewards.snapshot.claims_snapshot.get_claimable_data", mock_get_claimable_data
    )
    # Make sure native and non-native balances are correcly calculated to usd
    for boost_chain in BOOST_CHAINS:
        responses.add(
            responses.GET,
            f"{badger_api}/prices?chain={boost_chain}",
            json={
                BADGER: BADGER_PRICE,
                BCVXCRV: CVX_CRV_PRICE,
                XSUSHI: XSUSHI_PRICE,
                DIGG: DIGG_PRICE,
                WBTC: WBTC_PRICE,
                ARB_BSWAPR_WETH_SWAPR: SWAPR_WETH_SWAPR_PRICE,
            },
            status=200,
        )
    responses.add_passthru("https://")
    native, non_native = claims_snapshot_usd(Network.Ethereum, claimable_block)
    expected_native_balance = 0
    # For this wallet native balance is only
    for claim in CLAIMABLE_BALANCES_DATA_ETH["rewards"][TEST_WALLET]:
        if claim["address"] == BADGER:
            expected_native_balance = (
                BADGER_PRICE * int(claim["balance"]) / math.pow(10, 18)
            )
    assert native[TEST_WALLET] == approx(Decimal(expected_native_balance))

    # For this wallet non-native balance is only cvxCRV token
    expected_non_native_balance = 0
    for claim in CLAIMABLE_BALANCES_DATA_ETH["rewards"][TEST_WALLET]:
        if claim["address"] == BCVXCRV:
            expected_non_native_balance = (
                CVX_CRV_PRICE * int(claim["balance"]) / math.pow(10, 18)
            )
    assert non_native[TEST_WALLET] == approx(Decimal(expected_non_native_balance))
