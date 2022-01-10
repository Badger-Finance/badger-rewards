import responses

from badger_api.requests import (
    badger_api,
    fetch_ppfs,
    fetch_token,
    fetch_token_names,
    fetch_token_prices,
)
from helpers.constants import BOOST_CHAINS
from rewards.explorer import fetch_block_by_timestamp


@responses.activate
def test_fetch_block_by_timestamp_handled(mock_discord):
    responses.add(
        responses.GET,
        "https://api.etherscan.io/api?module=block&action="
        "getblocknobytime&timestamp=123&closest=before&apikey=",
        json={},
        status=404,
    )
    fetch_block_by_timestamp("ethereum", 123)

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
    fetch_token_names("ethereum")
    assert mock_discord.call_count == 1
    assert not fetch_token("ethereum", "token")
