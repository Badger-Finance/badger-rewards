from config.env_config import env_config
from helpers.discord import send_message_to_discord
from rewards.boost.calc_boost import badger_boost
from rewards.aws.boost import add_user_data
from rich.console import Console

console = Console()

if __name__ == "__main__":
    currentBlock = env_config.web3.eth.block_number
    send_message_to_discord(
        "**CALCULATING NEW BOOST**", "Pulling data from the graph", [], "Boost Bot", False
    )
    boostData = badger_boost(currentBlock)
    add_user_data(userData=boostData)
