from rewards.tree_utils import get_last_proposed_cycle
from rewards.aws.helpers import get_secret
from config.env_config import env_config
from helpers.discord import send_message_to_discord
from helpers.constants import MONITORING_SECRET_NAMES
from rewards.calc_rewards import approve_root
from rich.console import Console

console = Console()


def approve_rewards(chain):
    discord_url = get_secret(
        MONITORING_SECRET_NAMES[chain], "DISCORD_WEBHOOK_URL", test=env_config.test
    )

    current_rewards, start_block, end_block = get_last_proposed_cycle(chain)
    if not current_rewards:
        return

    console.log(
        f"Generating rewards between {start_block} and {end_block} on {chain} chain"
    )
    send_message_to_discord(
        f"**Approving Rewards on {chain}**",
        f"Calculating rewards between {start_block} and {end_block}",
        [],
        "Rewards Bot",
        url=discord_url,
    )
    return approve_root(chain, start_block, end_block, current_rewards)
