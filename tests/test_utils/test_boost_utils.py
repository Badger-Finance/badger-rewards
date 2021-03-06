import pytest

from rewards.classes.Snapshot import Snapshot
from helpers.enums import Network
from config.constants import addresses
from rewards.boost.boost_utils import (
    calc_boost_balances,
    calc_union_addresses,
    filter_dust,
)
from conftest import (
    CHAIN_CLAIMS_SNAPSHOT_DATA,
    CHAIN_SETT_SNAPSHOT_DATA,
    NFT_SNAPSHOT_DATA,
)
from rewards.feature_flags.feature_flags import DIGG_BOOST, flags


@pytest.fixture
def mock_claims_and_ppfs(mocker):
    mocker.patch(
        "rewards.boost.boost_utils.claims_snapshot",
        return_value=({}),
    )
    mocker.patch(
        "rewards.classes.Snapshot.fetch_ppfs",
        return_value=(1.5, 1.5)
    )


def test_calc_boost_balances(mocker, chain, mock_snapshots, mock_claims_and_ppfs, fetch_token_mock):
    mocker.patch("rewards.boost.boost_utils.get_bvecvx_lp_ratio", return_value=1)
    mocker.patch("rewards.boost.boost_utils.get_bvecvx_lp_ppfs", return_value=1)
    mocker.patch("rewards.boost.boost_utils.digg_snapshot_usd", return_value={})
    snapshots = [Snapshot(addresses.BVECVX, {}), Snapshot(addresses.BVECVX_CVX_LP_SETT, {})]
    mocker.patch("rewards.boost.boost_utils.sett_snapshot", side_effect=snapshots)
    boost_balances = calc_boost_balances(
        123, Network.Ethereum
    )
    # Make sure snapshot balances are sum up for both nati
    sum_expected_native_balances = {}
    for key in CHAIN_CLAIMS_SNAPSHOT_DATA[0].keys():
        sum_expected_native_balances[key] = (
            CHAIN_CLAIMS_SNAPSHOT_DATA[0][key]
            + CHAIN_SETT_SNAPSHOT_DATA[0][key]
            + NFT_SNAPSHOT_DATA[key]
        )

    for addr, balance in sum_expected_native_balances.items():
        assert balance == boost_balances.native[addr]

    sum_expected_non_native_balances = {}
    for key in CHAIN_CLAIMS_SNAPSHOT_DATA[1].keys():
        sum_expected_non_native_balances[key] = (
            CHAIN_CLAIMS_SNAPSHOT_DATA[1][key] + CHAIN_SETT_SNAPSHOT_DATA[1][key]
        )

    for addr, balance in sum_expected_non_native_balances.items():
        assert balance == boost_balances.non_native[addr]

    for addr, balance in NFT_SNAPSHOT_DATA.items():
        assert boost_balances.nfts[addr] == balance

    if not flags.flag_enabled(DIGG_BOOST):
        assert boost_balances.digg == {}


def test_calc_boost_balances__dust_filtered(chain, mocker, mock_claims_and_ppfs, fetch_token_mock):
    snapshots = [Snapshot(addresses.BVECVX, {}), Snapshot(addresses.BVECVX_CVX_LP_SETT, {})]
    mocker.patch("rewards.boost.boost_utils.digg_snapshot_usd", return_value={})
    mocker.patch("rewards.boost.boost_utils.sett_snapshot", side_effect=snapshots)
    mocker.patch(
        "rewards.boost.boost_utils.token_snapshot_usd",
        return_value=(
            {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 0.1},
            {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 0.1},
        ),
    )
    mocker.patch(
        "rewards.boost.boost_utils.nft_snapshot_usd", return_value={}
    )
    mocker.patch("rewards.boost.boost_utils.get_bvecvx_lp_ratio", return_value=1)
    mocker.patch("rewards.boost.boost_utils.get_bvecvx_lp_ppfs", return_value=1)

    mocker.patch(
        "rewards.boost.boost_utils.chain_snapshot_usd",
        return_value=(
            {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 0.1},
            {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 0.1},
        ),
    )
    mocker.patch(
        "rewards.boost.boost_utils.claims_snapshot_usd",
        return_value=(
            {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 0.000001241234},
            {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 0.000001241234},
        ),
    )
    mocker.patch(
        "rewards.boost.boost_utils.fuse_snapshot_of_token",
        return_value=Snapshot(addresses.BVECVX, {
            "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 0.000001241234
        })
    )
    mocker.patch(
        "rewards.utils.snapshot_utils.digg_snapshot_usd",
        return_value={
            "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 0.000001241234
        }
    )

    boost_balances = calc_boost_balances(
        123, Network.Ethereum
    )

    assert boost_balances.native == {}
    assert boost_balances.non_native == {}
    assert boost_balances.nfts == {}
    assert boost_balances.bvecvx == {}
    assert boost_balances.digg == {}


def test_filter_dust():
    assert (
        filter_dust({"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 0.000001241234}, 2)
        == {}
    )
    assert filter_dust({"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 0.1}, 0) != {}


def test_calc_union_addresses():
    result = calc_union_addresses(
        {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 1},
        {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 1},
    )
    assert result == ["0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"]
    result = calc_union_addresses(
        {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 1},
        {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f561": 1},
    )
    assert set(result) == {
        "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56",
        "0x0000000000007F150Bd6f54c40A34d7C3d5e9f561",
    }
