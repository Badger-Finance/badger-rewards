from rewards.tree_utils import calc_next_cycle_range
from helpers.discord import send_message_to_discord
from helpers.constants import MONITORING_SECRET_NAMES
from rewards.aws.helpers import get_secret
from rewards.calc_rewards import propose_root
from config.env_config import env_config
from rich.console import Console

console = Console()


def propose_rewards(chain):
    discord_url = get_secret(
        MONITORING_SECRET_NAMES[chain], "DISCORD_WEBHOOK_URL", test=env_config.test
    )

    past_rewards, start_block, end_block = calc_next_cycle_range(chain)

    console.log(
        f"Generating rewards between {start_block} and {end_block} on {chain} chain"
    )
    send_message_to_discord(
        f"**Proposing Rewards on {chain}**",
        f"Calculating rewards between {start_block} and {end_block}",
        [],
        "Rewards Bot",
        url=discord_url,
    )
    propose_root(chain, start_block, end_block, past_rewards, save=False)
