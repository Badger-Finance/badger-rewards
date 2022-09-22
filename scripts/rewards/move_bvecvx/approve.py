import sys

from helpers.enums import Network
from logging_utils.logger import exception_logging
from scripts.rewards.move_bvecvx.move_bvecvx import move_bvecvx_func
from scripts.rewards.utils.custom_cycle import custom_eth_approve

sys.excepthook = exception_logging


if __name__ == "__main__":
    custom_eth_approve(Network.Ethereum, move_bvecvx_func, move_bvecvx_func)
