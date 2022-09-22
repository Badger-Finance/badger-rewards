import sys

from helpers.enums import Network
from logging_utils.logger import exception_logging
from scripts.rewards.migrate_rewards.migrate import migrate_func
from scripts.rewards.migrate_rewards.migrate import migrate_test
from scripts.rewards.utils.custom_cycle import custom_eth_approve

sys.excepthook = exception_logging


if __name__ == "__main__":
    custom_eth_approve(Network.Ethereum, migrate_func, migrate_test)
