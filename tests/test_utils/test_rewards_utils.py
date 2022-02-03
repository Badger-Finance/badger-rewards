from config.constants.addresses import BADGER
from helpers.enums import Network
from rewards.rewards_checker import token_diff_table_item, verify_rewards


def test_token_diff_table():
    table_item = token_diff_table_item(
        name="bBADGER",
        before=100,
        after=200,
        decimals=1
    )
    assert table_item == (100, [
        'bBADGER',
        '10.000000000000000000',
        '20.000000000000000000',
        '10.000000000000000000'
    ])


def test_verify_rewards__discord_get_called(mocker):
    discord = mocker.patch("rewards.rewards_checker.send_code_block_to_discord")
    mocker.patch(
        "rewards.rewards_checker.claims_snapshot",
        return_value={},
    )
    verify_rewards(
        past_tree={
            "endBlock": 123,
            'tokenTotals': {
                BADGER: 123,
            },
        },
        new_tree={
            "endBlock": 123,
            'tokenTotals': {
                BADGER: 123,
            },
        },
        chain=Network.Ethereum,
    )
    assert discord.call_count == 1
