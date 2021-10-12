from helpers.constants import BCVX, BCVXCRV
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

console = Console()

def check_negative_balances(merkle_tree, tree_manager):
    # Check if there are negative claimable rewards
    tokens_to_check = [BCVX, BCVXCRV]
    balances_to_fix = {}
    for addr, claims in merkle_tree["claims"].items():
        if any(token in tokens_to_check for token in claims["tokens"]):
            claimed = tree_manager.get_claimed_for(addr, [BCVX, BCVXCRV])
            bcvx_claimed = int(claimed[1][claimed[0].index(BCVX)])
            bcvx_crv_claimed = int(claimed[1][claimed[0].index(BCVXCRV)])
            if BCVX not in claims["tokens"]:
                bcvx_total = 0
            else:
                bcvx_total = int(claims["cumulativeAmounts"][claims["tokens"].index(BCVX)])
            if BCVXCRV not in claims["tokens"]:
                bcvxcrv_total = 0
            else:
                bcvxcrv_total = int(claims["cumulativeAmounts"][claims["tokens"].index(BCVXCRV)])
            
            claimable_bcvx = bcvx_total - bcvx_claimed
            claimable_bcvxcrv = bcvxcrv_total - bcvx_crv_claimed
            if claimable_bcvx < 0:
                if addr not in balances_to_fix:
                    balances_to_fix[addr] = {}
                balances_to_fix[addr][BCVX] = abs(claimable_bcvx)
            if claimable_bcvxcrv < 0:
                if addr not in balances_to_fix:
                    balances_to_fix[addr] = {}
                balances_to_fix[addr][BCVXCRV] = abs(claimable_bcvxcrv)
                
    with open("balances_to_fix.json", "w") as fp:
        json.dump(balances_to_fix, fp)
    return balances_to_fix

                
        
def fix_eth_rewards(): 
    chain = "eth"
    tree_file_name = "rewards-1-0xd00b9252eeb4b0a35a9e23b24f28a3154a09f1072f6b2f870796347eee844870.json"
    tree = json.load(open(tree_file_name))
    start_block = int(tree["endBlock"]) + 1
    end_block = 13398599
    
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    cycle_account = Account.from_key(cycle_key)

    tree_manager = TreeManager(chain, cycle_account)
    boosts = download_boosts()
    rewards_manager = RewardsManager("eth", tree_manager.next_cycle, start_block, end_block, boosts)
    print(start_block, end_block)
    
    ## Generate rewards for cycle
    rewards = generate_rewards_in_range(
        chain,
        start=start_block,
        end=end_block,
        save=False,
        past_tree=tree,
        tree_manager=tree_manager,
    )
    with open("intermediate_rewards.json", "w") as fp:
        json.dump(rewards["merkleTree"],fp)
    # convert to rewards list
    rewards_list = process_cumulative_rewards(rewards["merkleTree"], RewardsList(tree_manager.next_cycle))
    balances = check_negative_balances(rewards["merkleTree"], tree_manager)
    for addr, token_data in balances.items():
        for token, amount in token_data.items():
            rewards_list.increase_user_rewards(
               addr,
               token,
               amount
            )
    rewards_tree = rewards_to_merkle_tree(rewards_list, start_block, end_block)
    root_hash = rewards_manager.web3.keccak(text=rewards_tree["merkleRoot"])
    chain_id = rewards_manager.web3.eth.chain_id
    file_name = f"rewards-{chain_id}-{encode_hex(root_hash)}.json"
    
    bals = check_negative_balances(rewards_tree, tree_manager)
    assert len(bals) == 0
    console.log("No negative balances")
    
    return {
        "merkleTree": rewards_tree,
        "rootHash": root_hash.hex(),
        "fileName": file_name,
        "multiplierData": rewards_manager.get_sett_multipliers(),
        "userMultipliers": rewards_manager.get_user_multipliers(),
    } 

    
            
        
    
