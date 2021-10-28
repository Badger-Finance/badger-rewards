from subgraph.queries.setts import last_synced_block
from rewards.classes.TreeManager import TreeManager
from rich.console import Console
from helpers.enums import Network
from typing import List

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
    if chain == Network.Arbitrum:
        end_block = end_block - 100

    # Sanity check: Ensure start block is not too far in the past
    assert start_block < end_block

    # Sanity check: Ensure start block is not too close to end block
    return (current_rewards, start_block, end_block)


def calc_claimable_balances(
    tree_manager: TreeManager, tokens_to_check: List[str], merkle_tree
):
    balances = {}
    for addr, claim in merkle_tree["claims"].items():
        claimable_bals = user_claimable_balances(
            addr, claim, tree_manager, tokens_to_check
        )
        balances[addr] = claimable_bals
    return balances


def user_claimable_balances(
    user: str, claim, tree_manager: TreeManager, tokens_to_check
):
    claimable_balances = {}
    if any(token in tokens_to_check for token in claim["tokens"]):
        claimed = tree_manager.get_claimed_for(user, tokens_to_check)
        for token in tokens_to_check:
            claimed_token = int(claimed[1][claimed[0].index(token)])
            if token not in claim["tokens"]:
                claimable_balances[token] = 0
            else:
                total_token = int(
                    claim["cumulativeAmounts"][claim["tokens"].index(token)]
                )
                claimable_balances[token] = int(total_token) - int(claimed_token)

    return claimable_balances
