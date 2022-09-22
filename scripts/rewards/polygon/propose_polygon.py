import sys

from helpers.enums import Network
from logging_utils.logger import exception_logging
from scripts.rewards.utils.propose_rewards import propose_rewards

sys.excepthook = exception_logging

if __name__ == "__main__":
    propose_rewards(Network.Polygon)
