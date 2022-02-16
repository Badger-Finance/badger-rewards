from copy import deepcopy
import config.constants.addresses as addresses
from helpers.enums import Network
import pytest
from subgraph.queries.tokens import fetch_across_balances, fetch_fuse_pool_token
from tests.test_subgraph.test_data import ACROSS_BALANCES_TEST_DATA, FUSE_TOKEN_TEST_DATA


def test_fetch_across_balances(mocker):
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            deepcopy(ACROSS_BALANCES_TEST_DATA),
            {'tokenBalances': []}
        ],
    )
    across_multiplier = 1.2
    mocker.patch(
        "subgraph.queries.tokens.get_across_lp_multiplier",
        return_value=across_multiplier
    )
    expected_bals = {
        "0x1c1fd689103bbfd701b3b7d41a3807f12814033d": 341.22906723695934 * across_multiplier,
        "0x0x2b5455aac8d64c14786c3a29858e43b5945819c0": 1013.6019361743114 * across_multiplier
    }
    across_bals = fetch_across_balances(1728601720, Network.Ethereum)
    assert across_bals == expected_bals


def test_fetch_across_balances_empty(mocker):
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            {'tokenBalances': []}
        ],
    )
    across_bals = fetch_across_balances(1728601720, Network.Ethereum)
    assert across_bals == {}


@pytest.fixture
def mock_make_token(mocker):

    class Call:
        def __init__(self, value):
            self.value = value
            self.call = lambda: self.value

    class MockToken:
        def __init__(self, decimals, exchange_rate, _=None):
            self.decimals = lambda: Call(decimals)
            self.exchangeRateStored = lambda: Call(exchange_rate)

    mock_token = MockToken(18, 1.1, '')
    mocker.patch(
        "subgraph.queries.tokens.make_contract",
        return_value=mock_token
    )

    
def test_fetch_fuse_pool_token(mocker, mock_make_token):
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            deepcopy(FUSE_TOKEN_TEST_DATA),
            {'accountCTokens': []}
        ],
    )
    multiplier = 1.1
    expected_bals = {
        "0xC1e3EC0fE5A77aA7a264637B86C2E25182c82Daa": 300 * multiplier,
        "0x0279797ee0627d64FFa0D86f4f111F90E233B090": 1000 * multiplier
    }
    badger_fuse_balances = fetch_fuse_pool_token(Network.Ethereum, 1728601720, addresses.BADGER)
    assert badger_fuse_balances == expected_bals