from subgraph.queries.setts import last_synced_block
from rewards.classes.TreeManager import TreeManager
from config.rewards_config import rewards_config
from config.env_config import env_config
from rich.console import Console

console = Console()


def get_last_proposed_cycle(chain: str, tree_manager: TreeManager):
    if not tree_manager.has_pending_root():
        console.log("[bold yellow]===== No pending root, exiting =====[/bold yellow]")
        return ({}, 0, 0)

    console.log("Pending root found.. approving")

    # Fetch the appropriate file
    currentRewards = tree_manager.fetch_current_tree()

    lastClaimEnd = tree_manager.last_propose_end_block()
    lastClaimStart = tree_manager.last_propose_start_block()

    # Sanity check: Ensure previous cycle was not too long
    print(lastClaimStart)
    print(lastClaimEnd)
    # assert lastClaimStart > lastClaimEnd - rewards_config.maxStartBlockAge

    # Sanity check: Ensure previous end block is not too far in the past
    # assert lastClaimEnd > chain.height - rewards_config.maxStartBlockAge

    # Sanity check: Ensure start block is not too close to end block
    return (currentRewards, lastClaimStart, lastClaimEnd)


def calc_next_cycle_range(chain: str, tree_manager: TreeManager):
    # Fetch the appropriate file
    currentRewards = tree_manager.fetch_current_tree()

    lastClaimEnd = tree_manager.last_publish_end_block()
    startBlock = lastClaimEnd + 1

    # Claim at last synced block
    endBlock = last_synced_block(chain)
    print(endBlock)

    # Sanity check: Ensure start block is not too far in the past
    assert startBlock < endBlock

    # Sanity check: Ensure start block is not too close to end block
    return (currentRewards, startBlock, endBlock)
