import sys

from helpers.enums import Network
from logging_utils.logger import exception_logging
from scripts.rewards.retroactive_multisig_rewards.retroactive import retroactive_func
from scripts.rewards.retroactive_multisig_rewards.retroactive import test_retroactive_func
from scripts.rewards.utils.custom_cycle import custom_eth_approve

sys.excepthook = exception_logging


if __name__ == "__main__":
    custom_eth_approve(Network.Ethereum, retroactive_func, test_retroactive_func)
