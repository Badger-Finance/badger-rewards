import pytest

from helpers.constants import STAKE_RATIO_RANGES
from helpers.enums import Network
from rewards.boost.calc_boost import (
    badger_boost,
    calc_stake_ratio,
    get_badger_boost_data,
)


@pytest.fixture
def mock_discord_send_code(mocker):
    mocker.patch("rewards.boost.calc_boost.get_discord_url")
    return mocker.patch("rewards.boost.calc_boost.send_code_block_to_discord")


def test_calc_stake_ratio__happy():
    target = {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.1}
    assert calc_stake_ratio(
        "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56", target, target
    ) == list(target.values())[0] / list(target.values())[0]


def test_calc_stake_ratio__zero_native():
    target = {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.1}
    assert calc_stake_ratio(
        "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56",
        {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0},
        target,
    ) == 0


def test_calc_stake_ratio__zero_non_native():
    target = {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.1}
    assert calc_stake_ratio(
        "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56", target,
        {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0}
    ) == 0


def test_get_badger_boost_data():
    data, stake_data = get_badger_boost_data(
        {
            '0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 2000,
            '0x0000001d2B0A08A235276e8765aa1A659Aae58bb': 2000,
            '0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7909': 1,
            '0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f1111': 0,
        }
    )
    assert data['0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f1111'] == 1
    assert data['0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7909'] == 1800
    assert data['0x0000000000007F150Bd6f54c40A34d7C3d5e9f56'] == 2000
    assert stake_data[0] == 1
    assert stake_data[0.9] == 1
    assert stake_data[1] == 2


def test_badger_boost__happy(mock_discord_send_code, mock_snapshots):
    result = badger_boost(123, Network.Ethereum)
    assert mock_discord_send_code.called
    # Check boosts for different data points
    for addr, boost_data in result.items():
        if boost_data['stakeRatio'] == 0:
            assert boost_data['boost'] == 1
        elif boost_data['stakeRatio'] > 1:
            assert boost_data['boost'] == STAKE_RATIO_RANGES[-1][1]
        keys = list(boost_data.keys())
        assert 'boost' in keys
        assert 'nativeBalance' in keys
        assert 'nonNativeBalance' in keys
        assert 'nftBalance' in keys
        assert 'stakeRatio' in keys
        assert 'multipliers' in keys
        assert 'nfts' in keys
