from typing import Dict


class FlagNotFoundException(Exception):
    pass


TEST_FLAG_ENABLED = "TEST_FLAG_ENABLED"
BOOST_STEP = "BOOST_STEP"


class FeatureFlags:
    """
    Add new flags to FLAGS class attribute
    Flag format should be {str: bool}
    """
    FLAGS: Dict[str, bool] = {
        TEST_FLAG_ENABLED: True,
        BOOST_STEP: True,
    }

    def does_flag_exist(self, flag: str) -> bool:
        return self.FLAGS.get(flag, None)

    def flag_enabled(self, flag: str) -> bool:
        if self.does_flag_exist(flag) is None:
            raise FlagNotFoundException()
        return bool(self.FLAGS[flag])


flags = FeatureFlags()
