from decimal import Decimal

import pytest

from config.constants.addresses import BADGER
from config.constants.chain_mappings import SETTS
from config.constants.emissions import REWARD_ERROR_TOLERANCE
from helpers.enums import Network
from rewards.rewards_checker import assert_claims_increase
from rewards.rewards_checker import token_diff_table_item
from rewards.rewards_checker import verify_rewards
from rewards.utils.rewards_utils import check_token_totals_in_range
from rewards.utils.rewards_utils import get_actual_expected_totals
from rewards.utils.rewards_utils import get_claimed_for_token
from rewards.utils.rewards_utils import get_cumulative_claimable_for_token
from rewards.utils.rewards_utils import keccak

BVECVX = SETTS[Network.Ethereum]["bvecvx"]


def test_get_cumulative_claimable():
    cumulative = "1000"
    claimable = get_cumulative_claimable_for_token(
        {
            'tokens': [BADGER],
            'cumulativeAmounts': [cumulative],
        },
        BADGER
    )
    assert claimable == int(cumulative)


def test_get_cumulative_claimable__no_token():
    cumulative = "1000"
    claimable = get_cumulative_claimable_for_token(
        {
            'tokens': [BADGER],
            'cumulativeAmounts': [cumulative],
        },
        BVECVX
    )
    assert claimable == 0


def tests_get_claimed_for_token():
    user_claimed = 1000
    claimed = get_claimed_for_token(
        ([BADGER], [user_claimed]),
        BADGER
    )
    assert claimed == user_claimed


def test_keccak():
    assert keccak("123") == "0x64e604787cbf194841e7b68d7cd28786f6c9a0a3ab9f8b0a0e87cb4387ab0107"


def test_assert_claims_increase():
    assert_claims_increase(
        {
            'claims': {
                "0xaffb3b889E48745Ce16E90433A61f4bCb95692Fd": {
                    'tokens': [BADGER], 'cumulativeAmounts': [1000]
                }
            }
        },
        {
            'claims': {
                "0xaffb3b889E48745Ce16E90433A61f4bCb95692Fd": {
                    'tokens': [BADGER], 'cumulativeAmounts': [1000]
                }
            }
        },
    )


def test_assert_claims_increase_unhappy():
    with pytest.raises(AssertionError):
        assert_claims_increase(
            {
                'claims': {
                    "0xaffb3b889E48745Ce16E90433A61f4bCb95692Fd": {
                        'tokens': [BADGER], 'cumulativeAmounts': [1000]
                    }
                }
            },
            {
                'claims': {
                    "0xaffb3b889E48745Ce16E90433A61f4bCb95692Fd": {
                        'tokens': [BADGER], 'cumulativeAmounts': [100]
                    }
                }
            },
        )


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


def test_verify_rewards__discord_get_called(mocker, fetch_token_mock):
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
    ibbtc_sett = SETTS[Network.Ethereum]["ibbtc_crv"]
    cvxcrv_sett = SETTS[Network.Ethereum]["cvx_crv"]
    sett_totals = {
        ibbtc_sett: {
            "actual": {
                BADGER: Decimal(2e18),
                BVECVX: Decimal(1e18),
            },
            "expected": {
                BADGER: Decimal(2e18),
                BVECVX: Decimal(1e18),
            },
        },
        cvxcrv_sett: {
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

    sett_totals[ibbtc_sett]["expected"][BADGER] = Decimal(10e18)

    actual, expected = get_actual_expected_totals(sett_totals)

    assert actual == {
        BADGER: Decimal(4e18),
        BVECVX: Decimal(2e18)
    }
    assert expected == {
        BADGER: Decimal(12e18),
        BVECVX: Decimal(2e18)
    }


def test_check_token_totals_in_range(mocker, fetch_token_mock):
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

    invalid_totals = check_token_totals_in_range(Network.Ethereum, {})
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
    invalid_totals = check_token_totals_in_range(Network.Ethereum, {})
    actual = str(round(Decimal(2e18) / 10 ** 18, 5))
    token = BVECVX
    min_accepted = str(round(Decimal(3e18 * (1 - REWARD_ERROR_TOLERANCE)) / 10 ** 18, 5))
    max_accepted = str(round(Decimal(3e18 * (1 + REWARD_ERROR_TOLERANCE)) / 10 ** 18, 5))
    assert invalid_totals == [[token, min_accepted, max_accepted, actual]]
