import sys

from helpers.enums import Network
from logging_utils.logger import exception_logging
from scripts.rewards.utils.approve_rewards import approve_rewards

sys.excepthook = exception_logging


if __name__ == "__main__":
    approve_rewards(Network.Polygon)
