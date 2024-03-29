import os

from config.constants.chain_mappings import BOOST_BUFFER
from config.singletons import env_config
from helpers.discord import get_discord_url
from helpers.discord import send_message_to_discord
from helpers.enums import BotType
from helpers.enums import Network
from rewards.aws.boost import add_user_data
from rewards.boost.calc_boost import badger_boost


def generate_boosts(chain: Network):
    os.environ["BOT_TYPE"] = BotType.Boost
    current_block = env_config.get_web3(chain).eth.block_number
    current_block = current_block - BOOST_BUFFER.get(chain, 0)
    discord_url = get_discord_url(chain)
    send_message_to_discord(
        f"**CALCULATING NEW BOOST ({chain})**",
        "Pulling data from the graph",
        [],
        "Boost Bot",
        url=discord_url,
    )
    boost_data = badger_boost(current_block, chain)
    add_user_data(user_data=boost_data, chain=chain)
