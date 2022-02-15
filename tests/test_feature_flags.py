from rewards.feature_flags import flags


def test_flag_exists():
    assert flags.does_flag_exist("TEST_FLAG_ENABLED")
    assert not flags.does_flag_exist("SOME OTHER FLAG")
