from helpers.constants import BOOST_CHAINS
from config.env_config import env_config
from helpers.discord import send_message_to_discord
from rewards.boost.calc_boost import badger_boost
from rewards.aws.boost import add_user_data
from rich.console import Console

console = Console()

if __name__ == "__main__":
    currentBlock = env_config.get_web3().eth.block_number
    chains = ",".join(BOOST_CHAINS)
    send_message_to_discord(
        f"**CALCULATING NEW BOOST ({chains})**",
        "Pulling data from the graph",
        [],
        "Boost Bot",
    )
    boostData = badger_boost(currentBlock)
    add_user_data(userData=boostData)
