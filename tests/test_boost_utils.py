import pytest

from rewards.boost.boost_utils import (
    calc_boost_balances,
    calc_union_addresses,
    filter_dust,
)

TOKEN_SNAPSHOT_DATA = (
    {
        '0x01fb5de8847e570899d3e00029Ae9cD9cB40E5d7': 44557.11578,
        '0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7909': 4354.388194,
    },
    {
        '0x017b3763b8a034F8655D46345e3EB42555E39064': 0.000091143809567686612959,
        '0x01ebce016681D076667BDb823EBE1f76830DA6Fa': 0.000055073869881086331795,
    },
)

CHAIN_SETT_SNAPSHOT_DATA = (
    {
        '0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 2.0106850985422638,
        '0x0000001d2B0A08A235276e8765aa1A659Aae58bb': 44.602734829161123,
    },
    {
        '0x000E8C608473DCeE93021EB1d39fb4A7D7E7d780': 153519.6403430607008,
        '0x00369B46cd0c232Ff5dc1d376248c4954CE645Ee': 2102.2812933779145123,
    },
)

CHAIN_CLAIMS_SNAPSHOT_DATA = (
    {
        '0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 44557.11578,
        '0x0000001d2B0A08A235276e8765aa1A659Aae58bb': 4354.388194,
    },
    {
        '0x000E8C608473DCeE93021EB1d39fb4A7D7E7d780': 0.000091143809567686612959,
        '0x00369B46cd0c232Ff5dc1d376248c4954CE645Ee': 0.000055073869881086331795,
    },
)


@pytest.fixture
def mock_snapshots(mocker):
    mocker.patch(
        "rewards.boost.boost_utils.token_snapshot_usd",
        return_value=TOKEN_SNAPSHOT_DATA
    )
    mocker.patch(
        "rewards.boost.boost_utils.chain_snapshot_usd",
        return_value=CHAIN_SETT_SNAPSHOT_DATA
    )
    mocker.patch(
        "rewards.boost.boost_utils.claims_snapshot_usd",
        return_value=CHAIN_CLAIMS_SNAPSHOT_DATA
    )


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
    assert result == [
        '0x0000000000007F150Bd6f54c40A34d7C3d5e9f56', '0x0000000000007F150Bd6f54c40A34d7C3d5e9f561'
    ]
