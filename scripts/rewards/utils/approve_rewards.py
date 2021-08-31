from rewards.tree_utils import get_last_proposed_cycle
from rewards.classes.TreeManager import TreeManager
from config.env_config import env_config
from helpers.discord import send_message_to_discord
from rewards.calc_rewards import approve_root, propose_root
from rich.console import Console

console = Console()


def approve_rewards(chain):

    currentRewards, startBlock, endBlock = get_last_proposed_cycle(chain)
    console.log(
        "Generating rewards between {} and {} on {} chain".format(
            startBlock, endBlock, chain
        )
    )
    send_message_to_discord(
        "**Approving Rewards on {}**".format(chain),
        "Calculating rewards between {} and {}".format(startBlock, endBlock),
        [],
        "Rewards Bot",
    )
    return approve_root(chain, startBlock, endBlock, currentRewards)
