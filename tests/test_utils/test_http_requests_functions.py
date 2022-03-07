import pytest
import responses

from badger_api.requests import badger_api
from badger_api.requests import fetch_ppfs
from badger_api.requests import fetch_token
from badger_api.requests import fetch_token_names
from badger_api.requests import fetch_token_prices
from config.constants.chain_mappings import CHAIN_EXPLORER_URLS
from config.constants.emissions import BOOST_CHAINS
from helpers.enums import Network
from rewards.explorer import get_block_by_timestamp, fetch_block_by_timestamp
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


@pytest.mark.parametrize(
    "chain",
    [Network.Polygon, Network.Fantom, Network.Arbitrum, Network.Ethereum]
)
@responses.activate
def test_get_block_by_timestamp(mock_discord, chain):
    block = 100000
    timestamp = 1439799138
    # static timestamp for ETH for block 100000
    if chain != Network.Fantom:
        responses.add(
            responses.GET,
            f"https://api.{CHAIN_EXPLORER_URLS[chain]}/api?module=block&action="
            f"getblocknobytime&timestamp={timestamp}&closest=before&apikey=",
            json={
                'status': "1",
                'result': f"{block}"
            },
            status=200,
        )
    else:
        responses.add(
            responses.POST,
            "https://api.thegraph.com/subgraphs/name/elkfinance/ftm-blocks",
            json={
                'data': {'blocks': [{'timestamp': '1439799138', 'number': '100000'}]}
            },
            status=200,
        )
    data = get_block_by_timestamp(chain, timestamp)
    assert data == block


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Polygon, Network.Arbitrum]
)
def test_get_explorer_url(chain):
    assert get_explorer_url(chain, "0x123123") == (
        f"https://{CHAIN_EXPLORER_URLS[chain]}/tx/0x123123"
    )
