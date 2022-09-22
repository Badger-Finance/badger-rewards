import sys

from helpers.enums import Network
from logging_utils.logger import exception_logging
from scripts.rewards.clawback_digg.clawback import clawback_func
from scripts.rewards.clawback_digg.clawback import clawback_test
from scripts.rewards.utils.custom_cycle import custom_eth_approve

sys.excepthook = exception_logging


if __name__ == "__main__":
    custom_eth_approve(Network.Ethereum, clawback_func, clawback_test)
