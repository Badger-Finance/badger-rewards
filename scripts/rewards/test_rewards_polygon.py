from config.env_config import env_config
from helpers.discord import send_message_to_discord
from rewards.calc_rewards import generate_rewards_in_range
from rich.console import Console

console = Console()

if __name__ == "__main__":
    chain = "polygon"
    currentBlock = env_config.get_web3(chain).eth.block_number - 50
    startBlock = currentBlock - 500
    console.log("Generating rewards between {} and {} on {} chain".format(startBlock, currentBlock, chain))
    send_message_to_discord(
        "**CALCULATING Rewards on {}**".format(chain), "Calculating rewards between {} and {}".format(startBlock,currentBlock), [], "Rewards Bot"
    )
    generate_rewards_in_range(
        chain,
        startBlock,
        currentBlock,
    )
