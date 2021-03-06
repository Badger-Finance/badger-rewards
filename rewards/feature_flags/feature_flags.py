from typing import Dict


class FlagNotFoundException(Exception):
    pass


TEST_FLAG_ENABLED = "TEST_FLAG_ENABLED"
TEST_FLAG_DISABLED = "TEST_FLAG_DISABLED"
BOOST_STEP = "BOOST_STEP"
DIGG_BOOST = "DIGG_BOOST"


class FeatureFlags:
    """
    Add new flags to FLAGS class attribute
    Flag format should be {str: bool}
    """
    FLAGS: Dict[str, bool] = {
        TEST_FLAG_ENABLED: True,
        TEST_FLAG_DISABLED: False,
        BOOST_STEP: True,
        DIGG_BOOST: True
    }

    def flag_enabled(self, flag: str) -> bool:
        if self.FLAGS.get(flag) is None:
            raise FlagNotFoundException()
        return self.FLAGS[flag]


flags = FeatureFlags()
