import math
from decimal import Decimal

import pytest
import responses
from pytest import approx

from badger_api.requests import badger_api
from helpers.constants import (
    ARB_BADGER,
    BADGER,
    BOOST_CHAINS,
    CVX_CRV_ADDRESS,
    DIGG,
    NETWORK_TO_BADGER_TOKEN,
    POLY_BADGER,
    POLY_SUSHI,
    SWAPR_WETH_SWAPR_ARB_ADDRESS,
    XSUSHI,
)
from helpers.digg_utils import digg_utils
from helpers.enums import BalanceType, Network
from rewards.snapshot.claims_snapshot import claims_snapshot, claims_snapshot_usd

BADGER_PRICE = 27.411460272851376
XSUSHI_PRICE = 1.201460272851376
CVX_CRV_PRICE = 12.411460272851376
SWAPR_WETH_SWAPR_PRICE = 12312.201460272851376

TEST_WALLET = '0xD27E9195aA35A7dE31513656AD5d4D29268f94eC'
TEST_WALLET_ANOTHER = '0xF9e11762d522ea29Dd78178c9BAf83b7B093aacc'

CLAIMABLE_BALANCES_DATA_ETH = {
    'maxPage': 1,
    'rewards': {
        TEST_WALLET: [
            {
                'network': 'ethereum', 'address': BADGER,
                'balance': '148480869281534217908'
            },
            {
                'network': 'ethereum', 'address': CVX_CRV_ADDRESS,
                'balance': '2421328289687344724270258601055314109178877723910682205504219578892288'
            },
            {
                'network': 'ethereum', 'address': XSUSHI,
                'balance': '242132828968734472427025860105531410917'
            },
        ],
        TEST_WALLET_ANOTHER: [
            {
                'network': 'ethereum', 'address': BADGER,
                'balance': '8202381382803713155'
            },
            {
                'network': 'ethereum', 'address': CVX_CRV_ADDRESS,
                'balance': '2656585570737360069'
            },
            {
                'network': 'ethereum', 'address': XSUSHI,
                'balance': '4169175341925473404499430551565743649791614840189435481041751238508157'
            },
        ],
    }
}

CLAIMABLE_BALANCES_DATA_POLY = {
    'maxPage': 1,
    'rewards': {
        TEST_WALLET: [
            {
                'network': 'ethereum', 'address': POLY_BADGER,
                'balance': '148480869281534217908'
            },
            {
                'network': 'ethereum', 'address': POLY_SUSHI,
                'balance': '2421328289687344724270258601055314109178877723910682205504219578892288'
            },
        ],
        TEST_WALLET_ANOTHER: [
            {
                'network': 'ethereum', 'address': POLY_BADGER,
                'balance': '8202381382803713155'
            },
            {
                'network': 'ethereum', 'address': POLY_SUSHI,
                'balance': '2656585570737360069'
            },
        ],
    }
}

CLAIMABLE_BALANCES_DATA_ARB = {
    'maxPage': 1,
    'rewards': {
        TEST_WALLET: [
            {
                'network': 'ethereum', 'address': ARB_BADGER,
                'balance': '148480869281534217908'
            },
            {
                'network': 'ethereum', 'address': SWAPR_WETH_SWAPR_ARB_ADDRESS,
                'balance': '2421328289687344724270258601055314109178877723910682205504219578892288'
            },
        ],
        TEST_WALLET_ANOTHER: [
            {
                'network': 'ethereum', 'address': ARB_BADGER,
                'balance': '8202381382803713155'
            },
            {
                'network': 'ethereum', 'address': SWAPR_WETH_SWAPR_ARB_ADDRESS,
                'balance': '2656585570737360069'
            },
        ],
    }
}


@pytest.mark.parametrize(
    "chain, data",
    [
        (Network.Ethereum, CLAIMABLE_BALANCES_DATA_ETH),
        (Network.Polygon, CLAIMABLE_BALANCES_DATA_POLY),
        (Network.Arbitrum, CLAIMABLE_BALANCES_DATA_ARB),
    ]
)
@responses.activate
def test_claims_snapshot__happy(chain, data):
    responses.add(
        responses.GET, f"{badger_api}/accounts/allClaimable?page=1&chain={chain}",
        json=data, status=200
    )
    responses.add_passthru('https://')
    snapshots = claims_snapshot(chain)
    badger_snapshot = snapshots[NETWORK_TO_BADGER_TOKEN[chain]]
    assert badger_snapshot.type == BalanceType.Native
    assert badger_snapshot.ratio == 1
    assert badger_snapshot.token == NETWORK_TO_BADGER_TOKEN[chain]
    expected_badger_balance = 0
    for claim in data['rewards'][TEST_WALLET]:
        if claim['address'] == NETWORK_TO_BADGER_TOKEN[chain]:
            expected_badger_balance = int(claim['balance']) / math.pow(10, 18)
    assert badger_snapshot.balances[TEST_WALLET] == approx(Decimal(expected_badger_balance))

    excluded_token = None
    non_native_token = None
    if chain == Network.Ethereum:
        excluded_token = XSUSHI
        non_native_token = CVX_CRV_ADDRESS
    elif chain == Network.Polygon:
        excluded_token = POLY_SUSHI
    elif chain == Network.Arbitrum:
        excluded_token = SWAPR_WETH_SWAPR_ARB_ADDRESS
    for token in [excluded_token, non_native_token]:
        if token:
            snapshot = snapshots[excluded_token]
            assert snapshot.ratio == 1
            expected_token_balance = 0
            for claim in data['rewards'][TEST_WALLET]:
                if claim['address'] == excluded_token:
                    expected_token_balance = int(claim['balance']) / math.pow(10, 18)
            assert snapshot.balances[TEST_WALLET] == approx(
                Decimal(expected_token_balance)
            )


@responses.activate
def test_claims_snapshot_digg():
    # Digg has different calculation algorithm hence separate test
    balance = '148480869281534217908'
    responses.add(
        responses.GET, f"{badger_api}/accounts/allClaimable?page=1&chain={Network.Ethereum}",
        json={
            'maxPage': 1,
            'rewards': {
                TEST_WALLET: [
                    {
                        'network': 'ethereum', 'address': DIGG,
                        'balance': balance
                    },
                ]
            }
        }, status=200
    )
    responses.add_passthru('https://')
    snapshots = claims_snapshot(Network.Ethereum)
    digg_snapshot = snapshots[DIGG]
    assert digg_snapshot.type == BalanceType.Native
    assert digg_snapshot.ratio == 1
    assert digg_snapshot.token == DIGG
    expected_digg_balance = digg_utils.shares_to_fragments(int(balance)) / math.pow(10, 18)
    assert digg_snapshot.balances[TEST_WALLET] == approx(Decimal(expected_digg_balance))


@responses.activate
def test_claims_snapshot__unhappy(mock_discord):
    # Raises exception in case non-200 response is returned
    responses.add(
        responses.GET, f"{badger_api}/accounts/allClaimable?page=1&chain={Network.Ethereum}",
        json={'maxPage': 1}, status=400
    )
    responses.add_passthru('https://')
    with pytest.raises(ValueError):
        claims_snapshot(Network.Ethereum)


@responses.activate
def test_claims_snapshot_usd__happy():
    # Make sure native and non-native balances are correcly calculated to usd
    responses.add(
        responses.GET, f"{badger_api}/accounts/allClaimable?page=1&chain={Network.Ethereum}",
        json=CLAIMABLE_BALANCES_DATA_ETH, status=200
    )
    for boost_chain in BOOST_CHAINS:
        responses.add(
            responses.GET, f"{badger_api}/prices?chain={boost_chain}",
            json={
                BADGER: BADGER_PRICE,
                CVX_CRV_ADDRESS: CVX_CRV_PRICE,
                XSUSHI: XSUSHI_PRICE,
                SWAPR_WETH_SWAPR_ARB_ADDRESS: SWAPR_WETH_SWAPR_PRICE,
            },
            status=200
        )
    responses.add_passthru('https://')
    native, non_native = claims_snapshot_usd(Network.Ethereum)
    expected_native_balance = 0
    # For this wallet native balance is only
    for claim in CLAIMABLE_BALANCES_DATA_ETH['rewards'][TEST_WALLET]:
        if claim['address'] == BADGER:
            expected_native_balance = BADGER_PRICE * int(claim['balance']) / math.pow(10, 18)
    assert native[TEST_WALLET] == approx(Decimal(expected_native_balance))

    # For this wallet non-native balance is only cvxCRV token
    expected_non_native_balance = 0
    for claim in CLAIMABLE_BALANCES_DATA_ETH['rewards'][TEST_WALLET]:
        if claim['address'] == CVX_CRV_ADDRESS:
            expected_non_native_balance = CVX_CRV_PRICE * int(claim['balance']) / math.pow(10, 18)
    assert non_native[TEST_WALLET] == approx(Decimal(expected_non_native_balance))


@responses.activate
def test_claims_snapshot_usd__unhappy(mock_discord):
    # Raises exception in case non-200 response is returned
    responses.add(
        responses.GET, f"{badger_api}/accounts/allClaimable?page=1&chain={Network.Ethereum}",
        json={'maxPage': 1}, status=400
    )
    responses.add_passthru('https://')
    with pytest.raises(ValueError):
        claims_snapshot_usd(Network.Ethereum)
