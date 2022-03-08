import pytest

from rewards.feature_flags import flags
from rewards.feature_flags.feature_flags import (
    TEST_FLAG_DISABLED, TEST_FLAG_ENABLED, FlagNotFoundException
)


def test_flag_enabled():
    assert flags.flag_enabled(TEST_FLAG_ENABLED)


def test_flag_disabled():
    assert not flags.flag_enabled(TEST_FLAG_DISABLED)


def test_flag_enabled__unhappy():
    with pytest.raises(FlagNotFoundException):
        flags.flag_enabled("UNKNOWN_FLAG")
