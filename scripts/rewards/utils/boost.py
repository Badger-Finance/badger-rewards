from rich.console import Console
from config.constants.chain_mappings import BOOST_BUFFER

from config.singletons import env_config
from helpers.discord import get_discord_url, send_message_to_discord
from helpers.enums import BotType, Network
from rewards.aws.boost import add_user_data
from rewards.boost.calc_boost import badger_boost

console = Console()


def generate_boosts(chain: Network):
    current_block = env_config.get_web3(chain).eth.block_number
    current_block = current_block - BOOST_BUFFER.get(chain, 0)
    discord_url = get_discord_url(chain, BotType.Boost)
    send_message_to_discord(
        f"**CALCULATING NEW BOOST ({chain})**",
        "Pulling data from the graph",
        [],
        "Boost Bot",
        url=discord_url,
    )
    boost_data = badger_boost(current_block, chain)
    add_user_data(user_data=boost_data, chain=chain)
