from brownie import *
from helpers.discord import send_message_to_discord
from rewards.boost.calc_boost import badger_boost
from rewards.aws.boost import add_user_data
from rich.console import Console

console = Console()


def main():
    currentBlock = chain.height
    send_message_to_discord(
        "**CALCULATING NEW BOOST**",
        "Pulling data from the graph (with bsc)",
        [],
        "keepers/boostBot",
    )
    boostData = badger_boost(currentBlock)
    add_user_data(userData=boostData)
