from copy import deepcopy
import pytest
from helpers.enums import Network
from subgraph.queries.setts import fetch_chain_balances
from tests.test_subgraph.test_data import CHAIN_BALANCES_TEST_DATA
from tests.utils import TEST_WALLET
from config.constants import addresses


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Polygon, Network.Arbitrum]
)
def test_fetch_chain_balances_happy(mocker, chain):
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            deepcopy(CHAIN_BALANCES_TEST_DATA),
            {'userSettBalances': []}
        ],
    )
    block = 1234578
    balances = fetch_chain_balances(chain, block)
    assert balances[addresses.BCRV_IBBTC][TEST_WALLET] == 2000000000000 / 1e18
    assert balances[addresses.BCVXCRV][TEST_WALLET] == 100000000000 / 1e18


def test_fetch_chain_balances_raises(mocker):
    discord = mocker.patch(
        "subgraph.subgraph_utils.send_error_to_discord",
    )
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=Exception,
    )
    block = 14118623
    with pytest.raises(Exception):
        fetch_chain_balances(Network.Ethereum, block)
    assert discord.called
