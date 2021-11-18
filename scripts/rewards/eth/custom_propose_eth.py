from eth_account import Account
from rich.console import Console

from config.singletons import env_config
from helpers.discord import get_discord_url, send_message_to_discord
from helpers.enums import BotType, Network
from rewards.aws.helpers import get_secret
from rewards.aws.trees import download_latest_tree, upload_tree
from rewards.calc_rewards import propose_root
from rewards.classes.TreeManager import TreeManager
from rewards.utils.tree_utils import calc_next_cycle_range
from subgraph.queries.setts import last_synced_block

console = Console()


if __name__ == "__main__":
    chain = Network.Ethereum
    discord_url = get_discord_url(chain, BotType.Cycle)
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    cycle_account = Account.from_key(cycle_key)
    tree_manager = TreeManager(chain, cycle_account)
    end_block = last_synced_block(chain)

    past_rewards = download_latest_tree(chain)
    start_block = int(past_rewards["endBlock"]) + 1

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
    rewards_data = propose_root(chain, start_block, end_block, past_rewards, tree_manager, save=False)
    upload_tree(
                rewards_data["fileName"],
                rewards_data["merkleTree"],
                chain,
                staging=env_config.test or env_config.staging,
            )
