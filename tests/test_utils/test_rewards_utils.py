from helpers.constants import BADGER, SETTS, DEV_MULTISIG, ETH_BADGER_TREE
import pytest
from helpers.enums import Network
from rewards.rewards_checker import token_diff_table_item, verify_rewards
from rewards.classes.Snapshot import Snapshot
from rewards.utils.rewards_utils import distribute_rewards_to_snapshot
from decimal import Decimal


def test_token_diff_table():
    table_item = token_diff_table_item(
        name="bBADGER", before=100, after=200, decimals=1
    )
    assert table_item == (
        100,
        [
            "bBADGER",
            "10.000000000000000000",
            "20.000000000000000000",
            "10.000000000000000000",
        ],
    )


def test_verify_rewards__discord_get_called(mocker):
    discord = mocker.patch("rewards.rewards_checker.send_code_block_to_discord")
    mocker.patch(
        "rewards.rewards_checker.claims_snapshot",
        return_value={},
    )
    verify_rewards(
        past_tree={
            "endBlock": 123,
            "tokenTotals": {
                BADGER: 123,
            },
        },
        new_tree={
            "endBlock": 123,
            "tokenTotals": {
                BADGER: 123,
            },
        },
        chain=Network.Ethereum,
    )
    assert discord.call_count == 1


@pytest.mark.parametrize("token", [BADGER, SETTS[Network.Ethereum]["cvx_crv"]])
def test_distribute_rewards_to_snapshot_blacklist(token):
    amount = Decimal(5e18)
    user = "0xb794F5eA0ba39494cE839613fffBA74279579268"
    balances = {
        DEV_MULTISIG: 500,
        ETH_BADGER_TREE: 250,
        user: 500,
    }
    snapshot = Snapshot(token, balances)
    rewards = distribute_rewards_to_snapshot(amount, snapshot, token)
    if token == BADGER:
        assert rewards.claims[user][token] == amount
    elif token == SETTS[Network.Ethereum]["cvx_crv"]:
        half = amount / 2
        assert rewards.claims[user][token] == half
        assert rewards.claims[DEV_MULTISIG][token] == half
