from typing import Dict, Tuple
from rich.console import Console
from config.singletons import env_config
from badger_api.claimable import get_claimable_metadata
from rewards.classes.TreeManager import TreeManager
from subgraph.queries.setts import last_synced_block

console = Console()


def get_last_proposed_cycle(
    chain: str, tree_manager: TreeManager
) -> Tuple[Dict, int, int]:
    if not tree_manager.has_pending_root():
        console.log("[bold yellow]===== No pending root, exiting =====[/bold yellow]")
        return {}, 0, 0

    console.log("Pending root found.. approving")

    # Fetch the appropriate file
    current_rewards = tree_manager.fetch_current_tree()

    last_claim_end = tree_manager.last_propose_end_block()
    last_claim_start = tree_manager.last_propose_start_block()

    # Sanity check: Ensure start block is not too close to end block
    return current_rewards, last_claim_start, last_claim_end


def calc_next_cycle_range(
    chain: str, tree_manager: TreeManager
) -> Tuple[Dict, int, int]:
    # Fetch the appropriate file
    current_rewards = tree_manager.fetch_current_tree()
    last_claim_end = tree_manager.last_publish_end_block()
    if env_config.fix_cycle:
        start_block = int(current_rewards["endBlock"])
    else:
        start_block = last_claim_end + 1
    synced_block = last_synced_block(chain)
    metadata = get_claimable_metadata(chain, synced_block)
    end_block = metadata["endBlock"]
    assert end_block <= synced_block
    # Sanity check: Ensure start block is behind end block
    assert start_block < end_block

    return current_rewards, start_block, end_block
