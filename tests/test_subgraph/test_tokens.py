from helpers.enums import Network
from subgraph.queries.tokens import fetch_across_balances
from tests.test_subgraph.test_data import ACROSS_BALANCES_TEST_DATA
from copy import deepcopy

def test_fetch_across_balances(mocker):
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            deepcopy(ACROSS_BALANCES_TEST_DATA),
            {'tokenBalances': []}
        ],
    )
    mocker.patch(
        "subgraph.queries.tokens.get_across_lp_multiplier",
        return_value=1.2
    )
    expected_bals = {
        "0x1c1fd689103bbfd701b3b7d41a3807f12814033d": 409.4748806843512,
        "0x0x2b5455aac8d64c14786c3a29858e43b5945819c0": 1216.3223234091736
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
