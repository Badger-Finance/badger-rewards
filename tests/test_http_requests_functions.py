import pytest
import responses

from badger_api.requests import fetch_ppfs, fetch_token_prices
from helpers.constants import BOOST_CHAINS
from rewards.explorer import fetch_block_by_timestamp


@pytest.fixture
def mock_discord(mocker):
    return mocker.patch("helpers.http_session.send_message_to_discord")


@responses.activate
def test_fetch_block_by_timestamp_handled(mock_discord):
    responses.add(
        responses.GET, "https://api.etherscan.io/api?module=block&action="
                       "getblocknobytime&timestamp=123&closest=before&apikey=",
        json={}, status=404
    )
    fetch_block_by_timestamp("ethereum", 123)

    # Make sure discord message was sent
    assert mock_discord.called
    # Make sure only one message was sent to discord
    assert mock_discord.call_count == 1


@responses.activate
def test_fetch_ppfs_handled(mock_discord):
    responses.add(responses.GET, "https://staging-api.badger.com/v2/setts",
                  json={}, status=404)
    fetch_ppfs()

    # Make sure discord message was sent
    assert mock_discord.called
    # Make sure only one message was sent to discord
    assert mock_discord.call_count == 1


@responses.activate
def test_fetch_token_prices_handled(mock_discord):
    for chain in BOOST_CHAINS:
        responses.add(
            responses.GET, f"https://staging-api.badger.com/v2/prices?chain={chain}",
            json={}, status=404
        )
    fetch_token_prices()

    # Make sure discord message was sent
    assert mock_discord.called
    # Make sure len(BOOST_CHAINS) messages were sent to discord: one for each BOOST chain
    assert mock_discord.call_count == len(BOOST_CHAINS)
