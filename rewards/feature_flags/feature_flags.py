from typing import Dict


class FlagNotFoundException(Exception):
    pass


TEST_FLAG_ENABLED = "TEST_FLAG_ENABLED"


class FeatureFlags:
    """
    Add new flags to FLAGS class attribute
    Flag format should be {str: bool}
    """
    FLAGS: Dict[str, bool] = {
        TEST_FLAG_ENABLED: True
    }

    def does_flag_exist(self, flag: str) -> bool:
        return bool(self.FLAGS.get(flag))

    def flag_enabled(self, flag: str) -> bool:
        if not self.does_flag_exist(flag):
            raise FlagNotFoundException()
        return self.FLAGS[flag]


flags = FeatureFlags()
