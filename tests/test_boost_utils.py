from rewards.boost.boost_utils import (
    calc_boost_balances,
    calc_union_addresses,
    filter_dust,
)
from tests.conftest import CHAIN_CLAIMS_SNAPSHOT_DATA, CHAIN_SETT_SNAPSHOT_DATA


def test_calc_boost_balances(chain, mock_snapshots):
    native_balance, non_native_balances = calc_boost_balances(123, "whatever")
    # Make sure snapshot balances are sum up for both nati
    sum_expected_native_balances = {}
    for key in CHAIN_CLAIMS_SNAPSHOT_DATA[0].keys():
        sum_expected_native_balances[key] = CHAIN_CLAIMS_SNAPSHOT_DATA[0][key] \
                                        + CHAIN_SETT_SNAPSHOT_DATA[0][key]

    for addr, balance in sum_expected_native_balances.items():
        assert balance == native_balance[addr]
    sum_expected_non_native_balances = {}
    for key in CHAIN_CLAIMS_SNAPSHOT_DATA[1].keys():
        sum_expected_non_native_balances[key] = CHAIN_CLAIMS_SNAPSHOT_DATA[1][key] \
                                                + CHAIN_SETT_SNAPSHOT_DATA[1][key]

    for addr, balance in sum_expected_non_native_balances.items():
        assert balance == non_native_balances[addr]


def test_calc_boost_balances__dust_filtered(chain, mocker):
    mocker.patch(
        "rewards.boost.boost_utils.token_snapshot_usd",
        return_value=(
            {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.1},
            {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.1},
        )
    )
    mocker.patch(
        "rewards.boost.boost_utils.chain_snapshot_usd",
        return_value=(
            {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.1},
            {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.1},
        )
    )
    mocker.patch(
        "rewards.boost.boost_utils.claims_snapshot_usd",
        return_value=(
            {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.000001241234},
            {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.000001241234},
        )
    )
    native_balance, non_native_balances = calc_boost_balances(123, "whatever")
    assert native_balance == {}
    assert non_native_balances == {}


def test_filter_dust():
    assert filter_dust(
        {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.000001241234}, 2
    ) == {}
    assert filter_dust(
        {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.1}, 0
    ) != {}


def test_calc_union_addresses():
    result = calc_union_addresses(
        {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 1},
        {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 1}
    )
    assert result == ['0x0000000000007F150Bd6f54c40A34d7C3d5e9f56']
    result = calc_union_addresses(
        {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 1},
        {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f561': 1}
    )
    assert set(result) == {
        '0x0000000000007F150Bd6f54c40A34d7C3d5e9f56', '0x0000000000007F150Bd6f54c40A34d7C3d5e9f561'
    }
