import responses

from badger_api.requests import fetch_ppfs
from rewards.explorer import fetch_block_by_timestamp


@responses.activate
def test_fetch_block_by_timestamp_handled(mocker):
    discord = mocker.patch("helpers.http_session.send_message_to_discord")
    responses.add(responses.GET, "https://api.etherscan.io/api?module=block&action="
                                 "getblocknobytime&timestamp=123&closest=before&apikey=",
                  json={}, status=404)
    fetch_block_by_timestamp("ethereum", 123)

    # Make sure discord message was sent
    assert discord.called
    # Make sure only one message was sent to discord
    assert discord.call_count == 1


@responses.activate
def test_fetch_ppfs_handled(mocker):
    discord = mocker.patch("helpers.http_session.send_message_to_discord")
    responses.add(responses.GET, "https://staging-api.badger.com/v2/setts",
                  json={}, status=404)
    fetch_ppfs()

    # Make sure discord message was sent
    assert discord.called
    # Make sure only one message was sent to discord
    assert discord.call_count == 1
