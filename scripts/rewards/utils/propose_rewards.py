from rewards.tree_utils import calc_next_cycle_range
from helpers.discord import send_message_to_discord
from rewards.calc_rewards import propose_root
from rich.console import Console

console = Console()


def propose_rewards(chain):

    pastRewards, startBlock , endBlock = calc_next_cycle_range(chain)
    console.log(pastRewards)

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
    )
    propose_root(chain, startBlock, endBlock, pastRewards, save=True)
