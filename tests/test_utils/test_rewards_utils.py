from decimal import Decimal

from helpers.constants import BADGER, REWARD_ERROR_TOLERANCE, SETTS
from helpers.enums import Network
from rewards.rewards_checker import token_diff_table_item, verify_rewards
from rewards.utils.rewards_utils import (
    check_token_totals_in_range,
    get_actual_expected_totals,
)

BVECVX = SETTS[Network.Ethereum]["bvecvx"]

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

def test_get_actual_expected_totals():
    IBBTC_SETT = SETTS[Network.Ethereum]["ibbtc_crv"]
    CVXCRV_SETT = SETTS[Network.Ethereum]["cvx_crv"]
    sett_totals = {
        IBBTC_SETT: {
            "actual": {
                BADGER: Decimal(2e18), 
                BVECVX: Decimal(1e18), 
            },
            "expected": {
                BADGER: Decimal(2e18), 
                BVECVX: Decimal(1e18),
            },  
        },
        CVXCRV_SETT: {
            "actual": {
                BADGER: Decimal(2e18), 
                BVECVX: Decimal(1e18),
            },
            "expected": {
                BADGER: Decimal(2e18), 
                BVECVX: Decimal(1e18),
            },
        }
    }

    actual, expected = get_actual_expected_totals(sett_totals)

    assert actual == {
        BADGER: Decimal(4e18),
        BVECVX: Decimal(2e18)
    }
    assert expected == {
        BADGER: Decimal(4e18),
        BVECVX: Decimal(2e18)
    }

    sett_totals[IBBTC_SETT]["expected"][BADGER] = Decimal(10e18)

    actual, expected = get_actual_expected_totals(sett_totals)

    assert actual == {
        BADGER: Decimal(4e18),
        BVECVX: Decimal(2e18)
    }
    assert expected == {
        BADGER: Decimal(12e18),
        BVECVX: Decimal(2e18)
    }

def test_check_token_totals_in_range(mocker):
    mocker.patch(
        "rewards.utils.rewards_utils.get_actual_expected_totals",
        return_value=(
            {
                BADGER: Decimal(4e18),
                BVECVX: Decimal(2e18)
            },
            {
                BADGER: Decimal(4e18),
                BVECVX: Decimal(2e18)
            }
        ),
    )

    invalid_totals = check_token_totals_in_range({})
    assert invalid_totals == []

    mocker.patch(
        "rewards.utils.rewards_utils.get_actual_expected_totals",
        return_value=(
            {
                BADGER: Decimal(4e18),
                BVECVX: Decimal(2e18)
            },
            {
                BADGER: Decimal(4e18),
                BVECVX: Decimal(3e18)
            }
        ),
    )
    invalid_totals = check_token_totals_in_range({})
    actual = Decimal(2e18)
    expected = Decimal(3e18)
    token = BVECVX
    min_accepted = expected * Decimal(1 - REWARD_ERROR_TOLERANCE)
    max_accepted = expected * Decimal(1 + REWARD_ERROR_TOLERANCE)
    assert invalid_totals == [[token, min_accepted, max_accepted, actual]]