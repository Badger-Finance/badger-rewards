import math
from decimal import Decimal

import pytest
import responses
from pytest import approx

from badger_api.requests import badger_api
from helpers.constants import (
    ARB_BADGER,
    BADGER,
    CVX_CRV_ADDRESS,
    NETWORK_TO_BADGER_TOKEN,
    POLY_BADGER,
    POLY_SUSHI,
    SWAPR_WETH_SWAPR_ARB_ADDRESS,
    XSUSHI,
)
from helpers.enums import BalanceType, Network
from rewards.snapshot.claims_snapshot import claims_snapshot

TEST_WALLET = '0xD27E9195aA35A7dE31513656AD5d4D29268f94eC'
TEST_WALLET_ANOTHER = '0xF9e11762d522ea29Dd78178c9BAf83b7B093aacc'

CLAIMABLE_BALANCES_DATA_ETH = {
    'maxPage': 1,
    'rewards': {
        TEST_WALLET: [
            {
                'network': 'ethereum', 'address': BADGER,
                'balance': '148480869281534217908'},
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
                'balance': '8202381382803713155'},
            {
                'network': 'ethereum', 'address': CVX_CRV_ADDRESS,
                'balance': '2656585570737360069'},
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
                'balance': '148480869281534217908'},
            {
                'network': 'ethereum', 'address': POLY_SUSHI,
                'balance': '2421328289687344724270258601055314109178877723910682205504219578892288'
            },
        ],
        TEST_WALLET_ANOTHER: [
            {
                'network': 'ethereum', 'address': POLY_BADGER,
                'balance': '8202381382803713155'},
            {
                'network': 'ethereum', 'address': POLY_SUSHI,
                'balance': '2656585570737360069'},
        ],
    }
}

CLAIMABLE_BALANCES_DATA_ARB = {
    'maxPage': 1,
    'rewards': {
        TEST_WALLET: [
            {
                'network': 'ethereum', 'address': ARB_BADGER,
                'balance': '148480869281534217908'},
            {
                'network': 'ethereum', 'address': SWAPR_WETH_SWAPR_ARB_ADDRESS,
                'balance': '2421328289687344724270258601055314109178877723910682205504219578892288'
            },
        ],
        TEST_WALLET_ANOTHER: [
            {
                'network': 'ethereum', 'address': ARB_BADGER,
                'balance': '8202381382803713155'},
            {
                'network': 'ethereum', 'address': SWAPR_WETH_SWAPR_ARB_ADDRESS,
                'balance': '2656585570737360069'},
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
    expected_badger_balance_1 = 0
    for claim in data['rewards'][TEST_WALLET]:
        if claim['address'] == NETWORK_TO_BADGER_TOKEN[chain]:
            expected_badger_balance_1 = int(claim['balance']) / math.pow(10, 18)
    assert badger_snapshot.balances[TEST_WALLET] == approx(Decimal(expected_badger_balance_1))

    # TODO: More tests for non-native and excluded tokens