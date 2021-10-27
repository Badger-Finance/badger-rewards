from helpers.constants import BADGER, DIGG
from rewards.aws.boost import download_boosts
from rewards.calc_rewards import process_cumulative_rewards
from rewards.classes.MerkleTree import rewards_to_merkle_tree
from rewards.classes.RewardsList import RewardsList
from rewards.classes.RewardsManager import RewardsManager

from rewards.calc_rewards import generate_rewards_in_range
from config.env_config import env_config
from rewards.classes.TreeManager import TreeManager
import json
from rewards.aws.helpers import get_secret
from eth_account import Account
from eth_utils.hexadecimal import encode_hex
from rich.console import Console

from rewards.rewards_checker import verify_rewards

console = Console()

tokens_to_check = [BADGER,DIGG]

affected_addresses = list(json.load(open("affected_addresses.json")).keys())

def check_zero_balances(tree, balances, tree_manager):
    all_bals = {}
    i = 0
    for addr, token_info in balances.items():
        i = i + 1
        print(i)
        for token, amount in calculate_claimable_balances(addr, tree["claims"][addr], tree_manager).items():
            all_bals[token] = amount
            if token in token_info:
                console.log(addr ,token, amount)
                assert int(amount) == 0
    with open("all_claimable.json", "w") as fp:
        json.dump(all_bals, fp)
    console.log("ZERO BALANCES ")
    
def calculate_claimable_balances(user, claim, tree_manager: TreeManager):
    claimable_balances = {}
    if any(token in tokens_to_check for token in claim["tokens"]):
        claimed = tree_manager.get_claimed_for(tree_manager.w3.toChecksumAddress( user ), tokens_to_check)
        badger_claimed = int(claimed[1][claimed[0].index(BADGER)])
        digg_claimed = int(claimed[1][claimed[0].index(DIGG)])
        if BADGER not in claim["tokens"]:
            badger_total = 0
            claimable_balances[BADGER] = 0
        else:
            badger_total = int(claim["cumulativeAmounts"][claim["tokens"].index(BADGER)])
            claimable_badger = badger_total - badger_claimed
            claimable_balances[BADGER] = int(claimable_badger)

        if DIGG not in claim["tokens"]:
            digg_total = 0
            claimable_balances[DIGG] = 0

        else:
            digg_total = int(
                claim["cumulativeAmounts"][claim["tokens"].index(DIGG)]
            )
            claimable_digg = digg_total - digg_claimed
            claimable_balances[DIGG] = int(claimable_digg)

    return claimable_balances
        

def check_negative_balances(merkle_tree, tree_manager):
    
    """
    Check if a merkle tree produces negative claimable balances
    using the calculation
    
    claimable balance = cumulative amount - total_claimed
    """
    console.log("Checking negative balances")
    balances_to_fix = {}
    i = 0
    for addr, claim in merkle_tree["claims"].items():
        i = i + 1
        print(i)
        if addr in affected_addresses:
            claimable_bals = calculate_claimable_balances(addr, claim, tree_manager)
            for token, amount in claimable_bals.items():
                if int(amount) < 0:
                    if addr not in balances_to_fix:
                        balances_to_fix[addr] = {}
                    balances_to_fix[addr][token] = abs(amount)
    return balances_to_fix


def fix_eth_rewards(tree_manager: TreeManager):
    chain = "eth"
    tree = tree_manager.fetch_current_tree()
    start_block = int(tree["endBlock"]) + 1
    end_block = start_block
    
    boosts = download_boosts()
    rewards_manager = RewardsManager("eth", tree_manager.next_cycle, start_block, end_block, boosts)
    print(start_block, end_block)
    
    rewards_list = process_cumulative_rewards(tree, RewardsList(tree_manager.next_cycle))
    balances = check_negative_balances(tree, tree_manager)
    console.log(len(balances))
    with open("balances_to_fix.json", "w") as fp:
        json.dump(balances, fp)
        
    for addr, token_data in balances.items():
        for token, amount in token_data.items():
            ## Increase users rewards who claimed too much so that their claimable balances are no longer zero
            rewards_list.increase_user_rewards(
               addr,
               token,
               amount
            )
    rewards_tree = rewards_to_merkle_tree(rewards_list, start_block, end_block)
    root_hash = rewards_manager.web3.keccak(text=rewards_tree["merkleRoot"])
    chain_id = rewards_manager.web3.eth.chain_id
    file_name = f"rewards-{chain_id}-{encode_hex(root_hash)}.json"
    check_zero_balances(rewards_tree, balances, tree_manager)
    bals = check_negative_balances(rewards_tree, tree_manager)
    assert len(bals) == 0
    verify_rewards(tree, rewards_tree)
    ## Check that there are no more negative claimable balances with this tree
   
    
    console.log("No negative balances")
    
    return {
        "merkleTree": rewards_tree,
        "rootHash": root_hash.hex(),
        "fileName": file_name,
        "multiplierData": rewards_manager.get_sett_multipliers(),
        "userMultipliers": rewards_manager.get_user_multipliers(),
    } 

    
            
        
    
