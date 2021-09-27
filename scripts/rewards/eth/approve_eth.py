from rewards.tree_utils import get_last_proposed_cycle
from rewards.aws.helpers import get_secret
from config.env_config import env_config
from helpers.discord import send_message_to_discord
from helpers.constants import MONITORING_SECRET_NAMES
from rewards.classes.TreeManager import TreeManager
from rewards.calc_rewards import approve_root
from rich.console import Console

from eth_account import Account
import os

console = Console()


def approve_rewards(chain):
    discord_url = os.getenv("DISCORD_WEBHOOK_URL")
    key_decrypt_password = get_secret(
        os.getenv("DECRYPT_PASSWORD_ARN"),
        os.getenv("DECRYPT_PASSWORD_KEY"),
        test=env_config.test,
    )

    cycle_account = Account.decrypt(os.getenv("KEYFILE"), key_decrypt_password)
    # Account.from_key(cycle_key)
    tree_manager = TreeManager(chain, cycle_account)

    currentRewards, startBlock, endBlock = get_last_proposed_cycle(chain, tree_manager)
    if not currentRewards:
        return

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
        url=discord_url,
    )
    return approve_root(chain, startBlock, endBlock, currentRewards, tree_manager)


if __name__ == "__main__":
    approve_rewards("eth")
