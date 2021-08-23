from rewards.classes.TreeManager import TreeManager
from helpers.web3_utils import get_badger_tree
from rewards.aws.trees import download_latest_tree
from config.env_config import env_config
from helpers.discord import send_message_to_discord
from rewards.calc_rewards import propose_root
from rich.console import Console

console = Console()


def propose_rewards(chain):

    currentBlock = env_config.get_web3(chain).eth.block_number - 50
    treeManager = TreeManager(chain)
    startBlock = treeManager.fetch_current_merkle_data()["blockNumber"]

    console.log(
        "Generating rewards between {} and {} on {} chain".format(
            startBlock, currentBlock, chain
        )
    )
    send_message_to_discord(
        "**CALCULATING Rewards on {}**".format(chain),
        "Calculating rewards between {} and {}".format(startBlock, currentBlock),
        [],
        "Rewards Bot",
    )
    propose_root(chain, startBlock, currentBlock, save=True)
