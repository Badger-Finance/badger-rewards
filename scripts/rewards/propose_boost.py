from helpers.discord import send_message_to_discord
from rewards.boost.calc_boost import badger_boost
from rewards.aws.boost import add_user_data
from rich.console import Console
from web3.auto.infura import w3

console = Console()


def main():
    currentBlock = w3.eth.block_number
    send_message_to_discord('**CALCULATING NEW BOOST**', 'Pulling data from the graph', [], 'keepers/boostBot')
    boostData = badger_boost(currentBlock)
    add_user_data(userData=boostData)
