from decimal import Decimal

import pytest

from config.constants.emissions import STAKE_RATIO_RANGES
from helpers.enums import Network
from rewards.boost.calc_boost import allocate_bvecvx_to_users
from rewards.boost.calc_boost import (
    allocate_nft_balances_to_users,
    allocate_nft_to_users,
    assign_native_balances_to_users,
    assign_non_native_balances_to_users,
    assign_stake_ratio_to_users,
    badger_boost,
    calc_stake_ratio,
    get_badger_boost_data,
)
from rewards.classes.Boost import BoostBalances
from rewards.feature_flags import flags


TEST_USER = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"


@pytest.fixture
def mock_discord_send_code(mocker):
    mocker.patch("rewards.boost.calc_boost.get_discord_url")
    return mocker.patch("rewards.boost.calc_boost.send_code_block_to_discord")


def test_calc_stake_ratio__happy():
    target = {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": Decimal(0.1)}
    assert (
        calc_stake_ratio(TEST_USER, BoostBalances(target, target))
        == pytest.approx(list(target.values())[0] / list(target.values())[0])
    )


def test_allocate_bvecvx_to_users():
    user = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"
    bve_balances = {user: Decimal(100)}
    boost_info = {
        user: {
            'nativeBalance': Decimal(10)
        }
    }
    allocate_bvecvx_to_users(
        boost_info,
        bve_balances,
    )
    assert boost_info[user]['nativeBalance'] == Decimal(15)
    assert boost_info[user]['bveCvxBalance'] == Decimal(5)


def test_allocate_bvecvx_to_users__no_user_boost():
    user = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"
    bve_balances = {user: Decimal(100)}
    boost_info = {}
    allocate_bvecvx_to_users(
        boost_info,
        bve_balances,
    )
    assert boost_info.get(user) is None


def test_calc_stake_ratio__zero_native():
    target = {TEST_USER: 0.1}
    assert (
        calc_stake_ratio(
            TEST_USER,
            BoostBalances(
                {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": Decimal(0.0)},
                target
            )
        )
        == 0
    )


def test_calc_stake_ratio__zero_non_native():
    target = {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": Decimal(0.1)}
    assert (
        calc_stake_ratio(
            TEST_USER, BoostBalances(
                target, {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": Decimal(0.0)}
            )
        )
        == 0
    )


def test_get_badger_boost_data():
    data, stake_data = get_badger_boost_data(
        {
            "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 1.452,
            "0x0000001d2B0A08A235276e8765aa1A659Aae58bb": 1,
            "0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7909": 0.9,
            "0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7900": 0.2758,
            "0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f1111": 0,
        }
    )
    assert data["0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f1111"] == 1
    assert data["0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7909"] == 1800
    if flags.flag_enabled("BOOST_STEP"):
        assert data["0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7900"] == 551
    assert data["0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"] == 2000
    assert stake_data[0] == 1
    assert stake_data[0.9] == 1
    assert stake_data[1] == 2


def test_badger_boost__happy(mock_discord_send_code, mock_snapshots, mocker):
    mocker.patch(
        "rewards.boost.boost_utils.claims_snapshot",
        return_value=({}),
    )
    result = badger_boost(123, Network.Ethereum)
    assert mock_discord_send_code.called
    # Check boosts for different data points
    for addr, boost_data in result.items():
        if boost_data["stakeRatio"] == 0:
            assert boost_data["boost"] == 1
        elif boost_data["stakeRatio"] > 1:
            assert boost_data["boost"] == STAKE_RATIO_RANGES[-1][1]
        keys = list(boost_data.keys())
        assert "boost" in keys
        assert "nativeBalance" in keys
        assert "nonNativeBalance" in keys
        assert "nftBalance" in keys
        assert "stakeRatio" in keys
        assert "multipliers" in keys
        assert "nfts" in keys
        assert "bveCvxBalance" in keys


def test_allocate_nft_balances_to_users():
    boost = {TEST_USER: {}}
    allocate_nft_balances_to_users(boost, {TEST_USER: 123})
    assert boost[TEST_USER]["nftBalance"] == 123


def test_allocate_nft_to_users():
    boost = {TEST_USER: {}}
    allocate_nft_to_users(boost, [TEST_USER], {TEST_USER: 123})
    assert boost[TEST_USER]["nfts"] == 123


def test_allocate_nft_to_users__no_match():
    boost = {TEST_USER: {}}
    allocate_nft_to_users(boost, [], {TEST_USER: 123})
    assert boost[TEST_USER].get("nft") is None


def test_assign_stake_ratio_to_users():
    boost = {TEST_USER: {}}
    assign_stake_ratio_to_users(boost, {TEST_USER: 123})
    assert boost[TEST_USER]["stakeRatio"] == 123


def test_assign_native_balances_to_users():
    boost = {TEST_USER: {}}
    assign_native_balances_to_users(boost, {TEST_USER: 123})
    assert boost[TEST_USER]["nativeBalance"] == 123


def test_assign_nonnative_balances_to_users():
    boost = {TEST_USER: {}}
    assign_non_native_balances_to_users(boost, {TEST_USER: 123})
    assert boost[TEST_USER]["nonNativeBalance"] == 123
