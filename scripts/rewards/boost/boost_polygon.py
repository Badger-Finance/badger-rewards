import sys

from helpers.enums import Network
from logging_utils.logger import exception_logging
from scripts.rewards.utils.boost import generate_boosts

sys.excepthook = exception_logging


if __name__ == "__main__":
    generate_boosts(Network.Polygon)
