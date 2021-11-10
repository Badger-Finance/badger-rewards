from rewards.aws.trees import upload_tree
from rewards.classes.RewardsManager import RewardsManager
from rewards.classes.TreeManager import TreeManager
from rewards.classes.RewardsList import RewardsList
from rewards.classes.Schedule import Schedule
from rewards.rewards_utils import combine_rewards
from rewards.rewards_checker import verify_rewards
from rewards.aws.boost import add_multipliers, download_boosts
from rewards.aws.helpers import get_secret
from rewards.classes.CycleLogger import cycle_logger
from helpers.web3_utils import make_contract
from helpers.constants import (
    DISABLED_VAULTS,
    EMISSIONS_CONTRACTS,
)
from helpers.enums import Network, BotType
from helpers.discord import get_discord_url, send_message_to_discord
from subgraph.queries.setts import list_setts
from rich.console import Console
from config.singletons import env_config
from config.rewards_config import rewards_config
from eth_utils.hexadecimal import encode_hex
from hexbytes import HexBytes
from typing import List, Dict
from web3 import Web3
import json

console = Console()


def console_and_discord(msg: str, chain: str, bot_type: BotType = BotType.Cycle):
    url = get_discord_url(chain, bot_type)
    console.log(msg)
    send_message_to_discord("Rewards Cycle", msg, [], "Rewards Bot", url=url)


def parse_schedules(schedules) -> Dict[str, List[Schedule]]:
    """
    Parse unlock shcedules
    :param schedules: schedules to parse
    """
    schedules_by_token = {}
    console.log("Fetching schedules...")
    for s in schedules:
        schedule = Schedule(
            Web3.toChecksumAddress(s[0]),
            Web3.toChecksumAddress(s[1]),
            s[2],
            s[3],
            s[4],
            s[5],
        )
        if schedule.token not in schedules_by_token:
            schedules_by_token[schedule.token] = []
        schedules_by_token[schedule.token].append(schedule)
    return schedules_by_token


def fetch_all_schedules(chain: str, setts: List[str]):
    """
    Fetch all schedules on a particular chain
    :param chain: chain to fetch from
    :param setts: setts from which schedule to pull
    """
    logger = make_contract(
        EMISSIONS_CONTRACTS[chain]["RewardsLogger"], "RewardsLogger", chain
    )
    all_schedules = {}
    setts_with_schedules = []
    for sett in setts:
        schedules = logger.getAllUnlockSchedulesFor(sett).call()
        if len(schedules) > 0:
            setts_with_schedules.append(sett)
        all_schedules[sett] = parse_schedules(schedules)
    console.log(f"Fetched {len(all_schedules)} schedules")
    return all_schedules, setts_with_schedules


def fetch_setts(chain: str) -> List[str]:
    """
    Fetch setts that are eligible for rewards
    :param chain:
    """
    setts = list_setts(chain)
    return list(filter(lambda x: x not in DISABLED_VAULTS, setts))


def process_cumulative_rewards(current, new: RewardsList) -> RewardsList:
    """Combine past rewards with new rewards

    :param current: current rewards
    :param new: new rewards
    """
    result = RewardsList(new.cycle)

    # Add new rewards
    for user, claims in new.claims.items():
        for token, claim in claims.items():
            result.increase_user_rewards(user, token, claim)

    # Add existing rewards
    for user, user_data in current["claims"].items():
        for i in range(len(user_data["tokens"])):
            token = user_data["tokens"][i]
            amount = user_data["cumulativeAmounts"][i]
            result.increase_user_rewards(user, token, int(amount))

    # result.printState()
    return result


def propose_root(
    chain: str,
    start: int,
    end: int,
    past_rewards,
    tree_manager: TreeManager,
    save=False,
):
    """
    Propose a root on a chain

    :param chain: chain to propose root
    :param start: start block for rewards
    :param end: end block for rewards
    :param save: flag to save rewards file locally, defaults to False
    :type save: bool, optional
    """
    current_merkle_data = tree_manager.fetch_current_merkle_data()
    w3 = env_config.get_web3(chain)

    current_time = w3.eth.getBlock(w3.eth.block_number)["timestamp"]
    time_since_last_update = current_time - current_merkle_data["lastUpdateTime"]

    if time_since_last_update < rewards_config.root_update_interval(chain):
        console.log("[bold yellow]===== Last update too recent () =====[/bold yellow]")
    rewards_data = generate_rewards_in_range(
        chain, start, end, save=save, past_tree=past_rewards, tree_manager=tree_manager
    )
    console.log("Generated rewards")

    console.log(
        f"\n==== Proposing root with rootHash {rewards_data['rootHash']} ====\n"
    )
    if env_config.production:
        tx_hash, success = tree_manager.propose_root(rewards_data)


def approve_root(
    chain: str, start: int, end: int, current_rewards, tree_manager: TreeManager
):
    """Approve latest root on a chain

    :param chain: chain to approve root
    :param start: start block for rewards
    :param end: end block for rewards
    """
    cycle_logger.set_start_block(start)
    cycle_logger.set_end_block(end)

    rewards_data = generate_rewards_in_range(
        chain,
        start,
        end,
        save=False,
        past_tree=current_rewards,
        tree_manager=tree_manager,
    )
    if env_config.test or env_config.staging:
        add_multipliers(
            rewards_data["multiplierData"],
            rewards_data["userMultipliers"],
            chain=chain,
        )
        return rewards_data
    if tree_manager.matches_pending_hash(rewards_data["rootHash"]):
        console.log(
            f"\n==== Approving root with rootHash {rewards_data['rootHash']} ====\n"
        )

        tx_hash, success = tree_manager.approve_root(rewards_data, chain)
        cycle_logger.set_content_hash(rewards_data["rootHash"])
        cycle_logger.set_merkle_root(rewards_data["merkleTree"]["merkleRoot"])
        if success:
            upload_tree(
                rewards_data["fileName"],
                rewards_data["merkleTree"],
                chain,
                staging=env_config.test or env_config.staging,
            )

            add_multipliers(
                rewards_data["multiplierData"],
                rewards_data["userMultipliers"],
                chain=chain,
            )
            cycle_logger.save(tree_manager.next_cycle, chain)
            return rewards_data
    else:
        pending_hash = HexBytes(
            tree_manager.badger_tree.pendingMerkleContentHash().call()
        )
        console_and_discord(
            f"Approve hash {rewards_data['rootHash']} doesn't match pending hash {pending_hash.hex()}",
            chain,
        )
        return rewards_data


def generate_rewards_in_range(
    chain: str, start: int, end: int, save: bool, past_tree, tree_manager: TreeManager
):
    """Generate chain rewards for a chain within two blocks

    :param chain: chain to generate rewards
    :param start: start block for rewards
    :param end: end block for rewards
    :param save: flag to save file locally
    """
    all_schedules, setts = fetch_all_schedules(chain, fetch_setts(chain))

    console_and_discord(f"Generating rewards for {len(setts)} setts", chain)

    rewards_list = []
    boosts = download_boosts(chain)
    rewards_manager = RewardsManager(
        chain, tree_manager.next_cycle, start, end, boosts["userData"]
    )

    console.log("Calculating Tree Rewards...")
    tree_rewards = rewards_manager.calculate_tree_distributions()
    rewards_list.append(tree_rewards)

    console.log("Calculating Sett Rewards...")
    sett_rewards = rewards_manager.calculate_all_sett_rewards(setts, all_schedules)
    rewards_list.append(sett_rewards)
    if chain == Network.Ethereum:
        sushi_rewards = rewards_manager.calc_sushi_distributions()
        rewards_list.append(sushi_rewards)

    new_rewards = combine_rewards(rewards_list, rewards_manager.cycle)

    console.log("Combining cumulative rewards... \n")
    cumulative_rewards = process_cumulative_rewards(past_tree, new_rewards)

    console.log("Converting to merkle tree... \n")
    merkle_tree = tree_manager.convert_to_merkle_tree(cumulative_rewards, start, end)
    root_hash = rewards_manager.web3.keccak(text=merkle_tree["merkleRoot"])
    chain_id = rewards_manager.web3.eth.chain_id

    file_name = f"rewards-{chain_id}-{encode_hex(root_hash)}.json"

    verify_rewards(past_tree, merkle_tree, tree_manager, chain)

    if save:
        with open(file_name, "w") as fp:
            json.dump(merkle_tree, fp, indent=4)

    return {
        "merkleTree": merkle_tree,
        "rootHash": root_hash.hex(),
        "fileName": file_name,
        "multiplierData": rewards_manager.get_sett_multipliers(),
        "userMultipliers": rewards_manager.get_user_multipliers(),
    }
