from copy import deepcopy
import pytest
from helpers.enums import Network
from subgraph.queries.nfts import fetch_nfts
from tests.utils import TEST_WALLET
from tests.test_subgraph.test_data import NFT_TEST_DATA


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum]
)
def test_fetch_nfts(mocker, chain):
    block = 123456
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=[
            deepcopy(NFT_TEST_DATA),
            {'nftbalances': []}
        ]
    )
    nfts = fetch_nfts(chain, block)
    test_user_nft = nfts[TEST_WALLET][0]
    assert test_user_nft["id"] == "100"
    assert test_user_nft["address"] == "0x101B3fAc7d37a48E7C3A140f0Ce95eb6b234f8bf"


def test_fetch_nfts_incompatible_chain():
    assert fetch_nfts(Network.Polygon, 100) == {}


def test_fetch_nfts_raises(mocker):
    discord = mocker.patch(
        "subgraph.subgraph_utils.send_error_to_discord",
    )
    mocker.patch(
        "subgraph.subgraph_utils.Client.execute",
        side_effect=Exception,
    )
    block = 14118623
    with pytest.raises(Exception):
        fetch_nfts(Network.Ethereum, block)
    assert discord.called
