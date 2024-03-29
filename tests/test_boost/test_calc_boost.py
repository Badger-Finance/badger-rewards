import math
from decimal import Decimal
import pytest
from config.constants import addresses
from config.singletons import env_config
from helpers.enums import Network
from rewards.boost.calc_boost import allocate_bvecvx_to_users, allocate_digg_to_users
from rewards.boost.calc_boost import allocate_nft_balances_to_users
from rewards.boost.calc_boost import allocate_nft_to_users
from rewards.boost.calc_boost import assign_native_balances_to_users
from rewards.boost.calc_boost import assign_non_native_balances_to_users
from rewards.boost.calc_boost import assign_stake_ratio_to_users
from rewards.boost.calc_boost import badger_boost
from rewards.boost.calc_boost import calc_stake_ratio
from rewards.boost.calc_boost import get_badger_boost_data
from rewards.classes.Boost import BoostBalances
from rewards.classes.Snapshot import Snapshot
from rewards.feature_flags import flags
from rewards.feature_flags.feature_flags import BOOST_STEP
from unittest.mock import MagicMock

TEST_USER = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"


@pytest.fixture
def mock_discord_send_code(mocker):
    mocker.patch("rewards.boost.calc_boost.get_discord_url")
    return mocker.patch("rewards.boost.calc_boost.send_code_block_to_discord")


def test_calc_stake_ratio__happy():
    target = {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": Decimal(0.1)}
    assert calc_stake_ratio(TEST_USER, BoostBalances(target, target)) == pytest.approx(
        list(target.values())[0] / list(target.values())[0]
    )


def test_allocate_bvecvx_to_users():
    user = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"
    base_native_balances = {user: Decimal(10)}
    bve_balances = {user: Decimal(100)}
    boost_info = {user: {"nativeBalance": Decimal(10)}}
    allocate_bvecvx_to_users(
        boost_info,
        bve_balances,
        base_native_balances,
    )
    assert boost_info[user]["nativeBalance"] == Decimal(15)
    assert boost_info[user]["bveCvxBalance"] == Decimal(5)


def test_allocate_bvecvx_to_users__no_user_boost():
    user = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"
    base_native_balances = {}
    bve_balances = {user: Decimal(100)}
    boost_info = {}
    allocate_bvecvx_to_users(
        boost_info,
        bve_balances,
        base_native_balances,
    )
    assert boost_info.get(user) is None


def test_allocate_digg_to_users():
    user = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"
    base_native_balances = {user: Decimal(10)}
    digg_balances = {user: Decimal(100)}
    boost_info = {user: {"nativeBalance": Decimal(10)}}
    allocate_digg_to_users(
        boost_info,
        digg_balances,
        base_native_balances,
    )
    assert boost_info[user]["nativeBalance"] == Decimal(20)
    assert boost_info[user]["diggBalance"] == Decimal(10)


def test_allocate_digg_to_users__no_user_boost():
    user = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"
    base_native_balances = {}
    digg_balances = {user: Decimal(100)}
    boost_info = {}
    allocate_digg_to_users(
        boost_info,
        digg_balances,
        base_native_balances,
    )
    assert boost_info.get(user) is None


def test_allocate_digg_to_users_equal_balance():
    user = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"
    base_native_balances = {user: Decimal(100)}
    digg_balances = {user: Decimal(100)}
    boost_info = {user: {"nativeBalance": Decimal(100)}}
    allocate_digg_to_users(
        boost_info,
        digg_balances,
        base_native_balances,
    )
    assert boost_info[user]["nativeBalance"] == Decimal(200)
    assert boost_info[user]["diggBalance"] == Decimal(100)


def test_allocate_digg_to_users_no_digg():
    user = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"
    base_native_balances = {user: Decimal(100)}
    digg_balances = {}
    boost_info = {user: {"nativeBalance": Decimal(100)}}
    allocate_digg_to_users(
        boost_info,
        digg_balances,
        base_native_balances,
    )
    assert boost_info[user]["nativeBalance"] == Decimal(100)
    assert "diggBalance" not in boost_info[user]


def test_allocate_digg_to_users_less_digg():
    user = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"
    base_native_balances = {user: Decimal(100)}
    digg_balances = {user: Decimal(50)}
    boost_info = {user: {"nativeBalance": Decimal(100)}}
    allocate_digg_to_users(
        boost_info,
        digg_balances,
        base_native_balances,
    )
    assert boost_info[user]["nativeBalance"] == Decimal(150)
    assert boost_info[user]["diggBalance"] == Decimal(50)


def test_allocate_no_mutate():
    user = "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"
    base_native_balances = {user: Decimal(100)}
    digg_balances = {user: Decimal(1000)}
    bve_balances = {user: Decimal(100)}
    boost_info = {user: {"nativeBalance": Decimal(100)}}
    allocate_bvecvx_to_users(
        boost_info,
        bve_balances,
        base_native_balances,
    )
    assert boost_info[user]["nativeBalance"] == Decimal(150)
    assert boost_info[user]["bveCvxBalance"] == Decimal(50)

    allocate_digg_to_users(
        boost_info,
        digg_balances,
        base_native_balances,
    )
    assert boost_info[user]["nativeBalance"] == Decimal(250)
    assert boost_info[user]["diggBalance"] == Decimal(100)


def test_calc_stake_ratio__zero_native():
    target = {TEST_USER: 0.1}
    assert (
        calc_stake_ratio(
            TEST_USER,
            BoostBalances(
                {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": Decimal(0.0)}, target
            ),
        )
        == 0
    )


def test_calc_stake_ratio__zero_non_native():
    target = {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": Decimal(0.1)}
    assert (
        calc_stake_ratio(
            TEST_USER,
            BoostBalances(
                target, {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": Decimal(0.0)}
            ),
        )
        == 0
    )


def test_get_badger_boost_data():
    data, stake_data = get_badger_boost_data(
        {
            "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": Decimal(1.452),
            "0x0000001d2B0A08A235276e8765aa1A659Aae58bb": Decimal(1),
            "0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7909": Decimal(0.9),
            "0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7900": Decimal(0.2758),
            "0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f1111": Decimal(0),
            "0x285C39e344179C253a75761C6737dE92183fA1F2": Decimal(1.25),
            "0x0069f94C6Ef196cf54b2f0746dE92D40a83D41A5": Decimal(1.75),
            "0x5E9F7E92e742F73b990dCa63c88325eD24666E84": Decimal(2.5),
            "0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8": Decimal(3.5),
        }
    )
    assert data["0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f1111"] == 1
    assert data["0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7909"] == 1800
    if flags.flag_enabled(BOOST_STEP):
        assert data["0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7900"] == 551
        assert data["0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f1111"] == 1
        assert data["0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7909"] == math.floor(
            0.9 * 2000
        )
        assert data["0x285C39e344179C253a75761C6737dE92183fA1F2"] == 2250
        assert data["0x0069f94C6Ef196cf54b2f0746dE92D40a83D41A5"] == 2625
        assert data["0x5E9F7E92e742F73b990dCa63c88325eD24666E84"] == 2875
        assert data["0xEA674fdDe714fd979de3EdF0F56AA9716B898ec8"] == 3000

    else:
        assert data["0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7900"] == 500
        assert data["0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"] == 2000
        assert stake_data[0] == 1
        assert stake_data[0.9] == 1
        assert stake_data[1] == 5


def test_badger_boost__happy(
    mock_discord_send_code,
    mock_snapshots,
    mocker,
    fetch_token_mock,
    mock_get_token_weight,
):
    mocker.patch("rewards.classes.Snapshot.fetch_ppfs", return_value=(1.2, 1.2))
    snapshots = [
        Snapshot(addresses.BVECVX, {}),
        Snapshot(addresses.BVECVX_CVX_LP_SETT, {}),
    ]
    mocker.patch("rewards.boost.boost_utils.sett_snapshot", side_effect=snapshots)
    mocker.patch("rewards.boost.boost_utils.digg_snapshot_usd", return_value={})

    mocker.patch(
        "rewards.boost.boost_utils.claims_snapshot",
        return_value=({}),
    )
    mocker.patch("rewards.boost.calc_boost.fetch_nfts", return_value={})
    mocker.patch("rewards.boost.boost_utils.get_bvecvx_lp_ratio", return_value=1)
    mocker.patch("rewards.boost.boost_utils.get_bvecvx_lp_ppfs", return_value=1)
    env_config.get_web3 = MagicMock(
        return_value=MagicMock(
            eth=MagicMock(get_block=MagicMock(return_value={"timestamp": 664582390}))
        )
    )

    result = badger_boost(123, Network.Ethereum)
    assert mock_discord_send_code.called
    # Check boosts for different data points
    for addr, boost_data in result.items():
        if boost_data["stakeRatio"] == 0:
            assert boost_data["boost"] == 1
        keys = list(boost_data.keys())
        assert "boost" in keys
        assert "nativeBalance" in keys
        assert "nonNativeBalance" in keys
        assert "nftBalance" in keys
        assert "stakeRatio" in keys
        assert "multipliers" in keys
        assert "nfts" in keys
        assert "bveCvxBalance" in keys
        assert "diggBalance" in keys


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
