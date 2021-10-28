from subgraph.queries.setts import last_synced_block
from rewards.classes.TreeManager import TreeManager
from rich.console import Console
from typing import List
from helpers.constants import CLAIMS_TO_CHECK
import random

console = Console()


def get_last_proposed_cycle(chain: str, tree_manager: TreeManager):
    if not tree_manager.has_pending_root():
        console.log("[bold yellow]===== No pending root, exiting =====[/bold yellow]")
        return ({}, 0, 0)

    console.log("Pending root found.. approving")

    # Fetch the appropriate file
    current_rewards = tree_manager.fetch_current_tree()

    last_claim_end = tree_manager.last_propose_end_block()
    last_claim_start = tree_manager.last_propose_start_block()

    # Sanity check: Ensure previous cycle was not too long
    # assert lastClaimStart > lastClaimEnd - rewards_config.maxStartBlockAge

    # Sanity check: Ensure previous end block is not too far in the past
    # assert lastClaimEnd > chain.height - rewards_config.maxStartBlockAge

    # Sanity check: Ensure start block is not too close to end block
    return (current_rewards, last_claim_start, last_claim_end)


def calc_next_cycle_range(chain: str, tree_manager: TreeManager):
    # Fetch the appropriate file
    current_rewards = tree_manager.fetch_current_tree()

    last_claim_end = tree_manager.last_publish_end_block()
    start_block = last_claim_end + 1

    # Claim at last synced block
    end_block = last_synced_block(chain)
    if chain == "arbitrum":
        end_block = end_block - 100

    # Sanity check: Ensure start block is not too far in the past
    assert start_block < end_block

    # Sanity check: Ensure start block is not too close to end block
    return (current_rewards, start_block, end_block)
