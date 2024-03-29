import json
import sys
import traceback

from decouple import config
from eth_account import Account

from helpers.discord import console_and_discord
from helpers.discord import send_message_to_discord
from helpers.enums import DiscordRoles
from helpers.enums import Network
from logging_utils import logger
from logging_utils.logger import exception_logging
from rewards.aws.helpers import get_secret
from rewards.calc_rewards import approve_root
from rewards.classes.TreeManager import TreeManager
from rewards.utils.tree_utils import get_last_proposed_cycle

sys.excepthook = exception_logging


def approve_rewards(chain, kube):
    discord_url = config("DISCORD_WEBHOOK_URL")
    key_decrypt_password = get_secret(
        "DECRYPT_PASSWORD_ARN",
        "DECRYPT_PASSWORD_KEY",
        region_name="us-west-2",
        kube=kube,
    )

    with open(config("KEYFILE")) as key_file:
        key_file_json = json.load(key_file)

    cycle_key = Account.decrypt(key_file_json, key_decrypt_password)
    cycle_account = Account.from_key(cycle_key)
    tree_manager = TreeManager(chain, cycle_account)
    if tree_manager.has_pending_root():
        logger.info("pending root, start approve rewards")
        currentRewards, startBlock, endBlock = get_last_proposed_cycle(
            chain, tree_manager
        )
        if not currentRewards:
            return

        logger.info(
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
    else:
        logger.info("no pending root, exiting")


if __name__ == "__main__":
    try:
        approve_rewards(Network.Ethereum, kube=False)
    except Exception:
        console_and_discord(
            f"Approve Error: \n {traceback.format_exc()}", Network.Ethereum,
            mentions=DiscordRoles.RewardsPod
        )
