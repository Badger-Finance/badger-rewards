import sys

from helpers.enums import Network
from logging_utils.logger import exception_logging
from scripts.rewards.redirect_rewards.redirect_rewards import redirect_rewards_func
from scripts.rewards.redirect_rewards.redirect_rewards import redirect_rewards_test
from scripts.rewards.utils.custom_cycle import custom_eth_approve

sys.excepthook = exception_logging


if __name__ == "__main__":
    custom_eth_approve(Network.Ethereum, redirect_rewards_func, redirect_rewards_test)
