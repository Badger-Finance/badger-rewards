from rewards.boost.calc_boost import calc_stake_ratio


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
