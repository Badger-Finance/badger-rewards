from web3 import Web3

from helpers.enums import Network
from subgraph.queries.harvests import fetch_tree_distributions
from tests.test_subgraph.test_data import BADGER_DISTRIBUTIONS_TEST_DATA


def test_fetch_tree_distributions_have_end_timestamp(mocker):
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            BADGER_DISTRIBUTIONS_TEST_DATA,
            {'badgerTreeDistributions': []}
        ],
    )
    strategy = BADGER_DISTRIBUTIONS_TEST_DATA['badgerTreeDistributions'][0]['strategy']['id']
    distributions = fetch_tree_distributions(1628601720, 1728601720, Network.Ethereum)
    for distribution in distributions:
        if distributions.index(distribution) == 0:
            assert distribution['end_of_previous_dist_timestamp'] == distribution['timestamp']
        else:
            assert distribution['end_of_previous_dist_timestamp'] == distributions[
                distributions.index(distribution) - 1
            ]['timestamp']
        assert distribution['strategy'] == Web3.toChecksumAddress(strategy)


def test_fetch_tree_distributions_empty_subgraph(mocker):
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            {'badgerTreeDistributions': []}
        ],
    )
    distributions = fetch_tree_distributions(1628601720, 1728601720, Network.Ethereum)
    assert distributions == []
