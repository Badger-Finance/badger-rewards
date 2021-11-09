from rewards.classes.TreeManager import TreeManager
from rewards.tree_utils import get_last_proposed_cycle
from rewards.aws.helpers import get_secret
from helpers.discord import get_discord_url, send_message_to_discord
from helpers.enums import BotType
from config.singletons import env_config
from eth_account import Account
from rewards.calc_rewards import approve_root
from rich.console import Console

console = Console()


def approve_rewards(chain):
    discord_url = get_discord_url(chain, BotType.Cycle)
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    cycle_account = Account.from_key(cycle_key)

    tree_manager = TreeManager(chain, cycle_account)
    current_rewards, start_block, end_block = get_last_proposed_cycle(
        chain, tree_manager
    )
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
    return approve_root(chain, start_block, end_block, current_rewards, tree_manager)
