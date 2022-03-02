import pytest
import responses

from badger_api.requests import badger_api
from badger_api.requests import fetch_ppfs
from badger_api.requests import fetch_token
from badger_api.requests import fetch_token_names
from badger_api.requests import fetch_token_prices
from config.constants import ARBITRUM_BLOCK_BUFFER
from config.constants import POLYGON_BLOCK_BUFFER
from config.constants import FANTOM_BLOCK_BUFFER
from config.constants.emissions import BOOST_CHAINS
from helpers.enums import Network
from rewards.explorer import CHAIN_EXPLORER_URLS
from rewards.explorer import convert_from_eth
from rewards.explorer import fetch_block_by_timestamp
from rewards.explorer import get_explorer_url


@responses.activate
def test_fetch_block_by_timestamp_handled(mock_discord):
    responses.add(
        responses.GET,
        "https://api.etherscan.io/api?module=block&action="
        "getblocknobytime&timestamp=123&closest=before&apikey=",
        json={},
        status=404,
    )
    fetch_block_by_timestamp(Network.Ethereum, 123)

    # Make sure discord message was sent
    assert mock_discord.called
    # Make sure only one message was sent to discord
    assert mock_discord.call_count == 1


@responses.activate
def test_fetch_ppfs_handled(mock_discord):
    responses.add(responses.GET, f"{badger_api}/setts", json={}, status=404)
    fetch_ppfs()

    # Make sure discord message was sent
    assert mock_discord.called
    # Make sure only one message was sent to discord
    assert mock_discord.call_count == 1


@responses.activate
def test_fetch_token_prices_handled(mock_discord):
    for chain in BOOST_CHAINS:
        responses.add(
            responses.GET, f"{badger_api}/prices?chain={chain}", json={}, status=404
        )
    fetch_token_prices()

    # Make sure discord message was sent
    assert mock_discord.called
    # Make sure len(BOOST_CHAINS) messages were sent to discord: one for each BOOST chain
    assert mock_discord.call_count == len(BOOST_CHAINS)


@responses.activate
def test_fetch_token_names_handled(mock_discord):
    responses.add(
        responses.GET, f"{badger_api}/tokens?chain=ethereum", json={}, status=404
    )
    fetch_token_names(Network.Ethereum)
    assert mock_discord.call_count == 1
    assert not fetch_token(Network.Ethereum, "token")


@responses.activate
def test_convert_from_eth(mock_discord):
    block = 100000
    timestamp = 1439799138
    responses.add_passthru("https://")
    for network in [Network.Ethereum, Network.Arbitrum, Network.Polygon]:
        # static timestamp for ETH for block 100000
        responses.add(
            responses.GET,
            f"https://api.{CHAIN_EXPLORER_URLS[network]}/api?module=block&action="
            f"getblocknobytime&timestamp={timestamp}&closest=before&apikey=",
            json={
                'status': "1",
                'result': f"{block}"
            },
            status=200,
        )
        responses.add(
            responses.POST,
            "https://api.thegraph.com/subgraphs/name/elkfinance/ftm-blocks",
            json={
                'data': {'blocks': [{'timestamp': '1439799138', 'number': '100000'}]}
            },
            status=200,
        )
    data = convert_from_eth(block)
    assert data[Network.Ethereum] == block
    assert data[Network.Polygon] == block - POLYGON_BLOCK_BUFFER
    assert data[Network.Arbitrum] == block - ARBITRUM_BLOCK_BUFFER
    assert data[Network.Fantom] == block - FANTOM_BLOCK_BUFFER


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Polygon, Network.Arbitrum]
)
def test_get_explorer_url(chain):
    assert get_explorer_url(chain, "0x123123") == (
        f"https://{CHAIN_EXPLORER_URLS[chain]}/tx/0x123123"
    )
