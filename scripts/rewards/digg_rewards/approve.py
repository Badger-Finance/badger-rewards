import sys

from helpers.enums import Network
from logging_utils.logger import exception_logging
from scripts.rewards.digg_rewards.digg import digg
from scripts.rewards.digg_rewards.digg import digg_test
from scripts.rewards.utils.custom_cycle import custom_eth_approve

sys.excepthook = exception_logging


if __name__ == "__main__":
    custom_eth_approve(Network.Ethereum, digg, digg_test)
