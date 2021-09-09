from rewards.tree_utils import calc_next_cycle_range
from helpers.discord import send_message_to_discord
from rewards.aws.helpers import get_secret
from rewards.calc_rewards import propose_root
from config.env_config import env_config
from rich.console import Console

console = Console()


def propose_rewards(chain):
    discord_url = get_secret(
        "cycle-bot/prod-discord-url", "DISCORD_WEBHOOK_URL", test=env_config.test
    )

    pastRewards, startBlock, endBlock = calc_next_cycle_range(chain)

    console.log(
        "Generating rewards between {} and {} on {} chain".format(
            startBlock, endBlock, chain
        )
    )
    send_message_to_discord(
        "**Proposing Rewards on {}**".format(chain),
        "Calculating rewards between {} and {}".format(startBlock, endBlock),
        [],
        "Rewards Bot",
        url=discord_url,
    )
    propose_root(chain, startBlock, endBlock, pastRewards, save=False)
