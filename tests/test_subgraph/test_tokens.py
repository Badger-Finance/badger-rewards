from copy import deepcopy
from unittest.mock import MagicMock

import pytest

from config.constants.addresses import (
    BADGER, FTM_BSMM_USDC_DAI
)
from helpers.enums import Network
from subgraph.queries.tokens import (
    fetch_across_balances,
    fetch_fuse_pool_token,
    fetch_token_balances,
)
from tests.test_subgraph.test_data import (
    ACROSS_BALANCES_TEST_DATA,
    TOKEN_BALANCES_TEST_DATA,
    TOKEN_BALANCES_TEST_DATA_ZERO_BALANCES,
    FUSE_TOKEN_TEST_DATA
)


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


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Polygon, Network.Arbitrum],
)
def test_fetch_token_balances_happy(mocker, chain):
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            deepcopy(TOKEN_BALANCES_TEST_DATA),
            {'tokenBalances': []},
        ],
    )
    tested_addr = "0x43298F9f91a4545dF64748e78a2c777c580573d6"
    block = 14118623
    badger_balances, digg_balances = fetch_token_balances(block, chain)
    assert badger_balances[tested_addr] == 21000000000000000000000000 / 1e18
    assert digg_balances[tested_addr] != 0


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Polygon, Network.Arbitrum],
)
def test_fetch_token_balances_zero_amounts(mocker, chain):
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            deepcopy(TOKEN_BALANCES_TEST_DATA_ZERO_BALANCES),
            {'tokenBalances': []},
        ],
    )
    block = 14118623
    badger_balances, digg_balances = fetch_token_balances(block, chain)
    assert digg_balances == {}
    assert badger_balances == {}


def test_fetch_token_balances_raises(mocker):
    discord = mocker.patch(
        "subgraph.subgraph_utils.send_error_to_discord"
    )
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=Exception,
    )
    block = 14118623
    with pytest.raises(Exception):
        fetch_token_balances(block, Network.Ethereum)
    assert discord.called


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Polygon, Network.Arbitrum],
)
def test_fetch_token_balances_empty(mocker, chain):
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            {'tokenBalances': []}
        ],
    )
    block = 14118623
    assert fetch_token_balances(block, chain) == ({}, {})


def fetch_fuse_pool_token_incompatible_chain():
    """
    Fuse token are available only on Ethereum
    """
    assert fetch_fuse_pool_token(Network.Polygon, 100, BADGER) == {}


def fetch_fuse_pool_token_no_token():
    assert fetch_fuse_pool_token(Network.Ethereum, 100, FTM_BSMM_USDC_DAI) == {}


def test_fetch_fuse_pool_token(mocker):
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            deepcopy(FUSE_TOKEN_TEST_DATA),
            {'accountCTokens': []}
        ],
    )
    multiplier = 1.1
    mocker.patch(
        "subgraph.queries.tokens.make_contract",
        return_value=MagicMock(
            exchangeRateStored=MagicMock(
                return_value=MagicMock(call=MagicMock(return_value=multiplier)),
            ),
            decimals=MagicMock(
                return_value=MagicMock(call=MagicMock(return_value=8)),
            )
        )
    )
    expected_bals = {
        "0xC1e3EC0fE5A77aA7a264637B86C2E25182c82Daa": 300 * multiplier,
        "0x0279797ee0627d64FFa0D86f4f111F90E233B090": 1000 * multiplier
    }
    badger_fuse_balances = fetch_fuse_pool_token(Network.Ethereum, 1728601720, BADGER)
    for addr, val in badger_fuse_balances.items():
        assert val == pytest.approx(expected_bals[addr])
