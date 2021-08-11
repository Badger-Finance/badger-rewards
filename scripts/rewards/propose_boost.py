from brownie import *
from rewards.boost.calc_boost import badger_boost
from rewards.aws.boost import add_user_data
from rich.console import Console

console = Console()


def main():
    currentBlock = chain.height - 50
    boostData = badger_boost(currentBlock)
    add_user_data(test=True, userData=boostData)
