from helpers.constants import BOOST_CHAINS
from config.env_config import env_config
from helpers.discord import send_message_to_discord
from rewards.boost.calc_boost import badger_boost
from rewards.aws.boost import add_user_data
from rich.console import Console

console = Console()

def generate_boosts(chain):
    current_block = env_config.get_web3(chain).eth.block_number
    send_message_to_discord(
        f"**CALCULATING NEW BOOST ({chain})**",
        "Pulling data from the graph",
        [],
        "Boost Bot",
    )
    boost_data = badger_boost(current_block, chain)
    add_user_data(user_data=boost_data, chain=chain)


