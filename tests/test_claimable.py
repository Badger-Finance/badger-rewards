import json

import pytest
from botocore.exceptions import ClientError
from moto.core import patch_resource

from badger_api.claimable import get_latest_claimable_snapshot
from helpers.enums import Network, SubgraphUrlType
from rewards.aws.helpers import dynamodb
from tests.utils import chains
from tests.utils import mock_tree
from tests.utils import set_env_vars

set_env_vars()


def mock_download_tree(file_name: str, chain: str):
    return json.dumps(mock_tree)


@pytest.fixture(autouse=True)
def mock_fns(mocker):
    mocker.patch("rewards.classes.TreeManager.download_tree", mock_download_tree)


@pytest.fixture
def tree():
    return mock_tree


@pytest.fixture
def tokens_to_check(tree):
    return list(tree["tokenTotals"].keys())


@pytest.mark.parametrize("chain", chains)
def test_get_latest_claimable_snapshot(chain, setup_dynamodb, mocker):
    url = f"https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-{chain}"
    if (chain == Network.Ethereum):
        url = "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts"
    mocker.patch("subgraph.subgraph_utils.subgraph_url",
                 return_value={SubgraphUrlType.Plain: url})
    patch_resource(dynamodb)
    cb_snapshot = get_latest_claimable_snapshot(chain)
    assert len(cb_snapshot) > 0
    for cb_data in cb_snapshot:
        assert 'address' in cb_data
        assert 'chain' in cb_data
        assert 'claimableBalances' in cb_data


def raise_client_error(chain, block):
    raise ClientError({}, "")


def test_latest_claimable_snapshot_unhappy(setup_dynamodb, mock_discord, mocker):
    patch_resource(dynamodb)
    mocker.patch("badger_api.claimable.get_claimable_balances", side_effect=raise_client_error)
    with pytest.raises(ClientError):
        get_latest_claimable_snapshot(Network.Ethereum)
        # Make sure discord message was sent
        assert mock_discord.called
        # Make sure only one message was sent to discord
        assert mock_discord.call_count == 1
