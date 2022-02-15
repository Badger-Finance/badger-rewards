import pytest

from rewards.feature_flags import flags
from rewards.feature_flags.feature_flags import FlagNotFoundException


def test_flag_exists():
    assert flags.does_flag_exist("TEST_FLAG_ENABLED")
    assert not flags.does_flag_exist("SOME OTHER FLAG")


def test_flag_enabled():
    assert flags.flag_enabled("TEST_FLAG_ENABLED")


def test_flag_enabled__unhappy():
    with pytest.raises(FlagNotFoundException):
        flags.flag_enabled("UNKNOWN_FLAG")
