from typing import Dict
from typing import List
from typing import Tuple

import simplejson as json
from eth_utils.hexadecimal import encode_hex
from hexbytes import HexBytes

from config.constants.chain_mappings import CHAIN_IDS
from config.constants.chain_mappings import EMISSIONS_CONTRACTS
from config.constants.emissions import NO_BOOST_CHAINS
from config.rewards_config import rewards_config
from config.singletons import env_config
from helpers.discord import console_and_discord
from helpers.enums import Abi
from helpers.web3_utils import make_contract
from rewards.aws.boost import add_multipliers
from rewards.aws.boost import download_boosts
from rewards.aws.boost import download_proposed_boosts
from rewards.aws.boost import upload_boosts
from rewards.aws.boost import upload_proposed_boosts
from rewards.aws.trees import upload_tree
from rewards.classes.RewardsManager import RewardsManager
from rewards.classes.Schedule import Schedule
from rewards.classes.TreeManager import TreeManager
from rewards.dynamo_handlers import put_rewards_data
from rewards.rewards_checker import verify_rewards
from rewards.snapshot.claims_snapshot import get_claimable_rewards_deficits
from logging_utils import logger as log
from rewards.utils.emission_utils import fetch_setts
from rewards.utils.emission_utils import get_schedules_by_token
from rewards.utils.emission_utils import parse_schedule
from rewards.utils.rewards_utils import combine_rewards
from rewards.utils.rewards_utils import process_cumulative_rewards


def fetch_all_schedules(
        chain: str, start: int, end: int
) -> Tuple[Dict[str, Dict[str, List[Schedule]]], List[str]]:
    """
    Fetch all schedules on a particular chain
    :param chain: chain to fetch from
    :param setts: setts from which schedule to pull
    """
    setts = fetch_setts(chain)
    logger = make_contract(
        EMISSIONS_CONTRACTS[chain]["RewardsLogger"], Abi.RewardsLogger, chain
    )
    w3 = env_config.get_web3(chain)
    start_timestamp = w3.eth.get_block(start)["timestamp"]
    end_timestamp = w3.eth.get_block(end)["timestamp"]
    all_schedules = {}
    setts_with_schedules = []
    for sett in setts:
        schedules = [parse_schedule(e) for e in logger.getAllUnlockSchedulesFor(sett).call()]
        for schedule in list(schedules):
            start_in_range = start_timestamp < schedule.startTime < end_timestamp
            end_in_range = start_timestamp < schedule.endTime < end_timestamp
            covers_range = schedule.startTime < start_timestamp and schedule.endTime > end_timestamp
            if start_in_range or end_in_range or covers_range:
                has_active_schedule = True
            else:
                schedules.remove(schedule)
        if len(schedules) > 0 and has_active_schedule:
            setts_with_schedules.append(sett)
        all_schedules[sett] = get_schedules_by_token(schedules)
    log.info(f"Fetched {len(all_schedules)} schedules")
    return all_schedules, setts_with_schedules


def propose_root(
        chain: str,
        start: int,
        end: int,
        past_rewards: Dict,
        tree_manager: TreeManager,
        save=False,
) -> None:
    """
    Propose a root on a chain

    :param chain: chain to propose root
    :param start: start block for rewards
    :param end: end block for rewards
    :param save: flag to save rewards file locally, defaults to False
    :param past_rewards: past rewards merkle tree
    :param tree_manager: TreeManager object
    :type save: bool, optional
    """
    current_merkle_data = tree_manager.fetch_current_merkle_data()
    w3 = env_config.get_web3(chain)

    current_time = w3.eth.get_block(w3.eth.block_number)["timestamp"]
    time_since_last_update = current_time - current_merkle_data["lastUpdateTime"]

    if time_since_last_update < rewards_config.root_update_interval(chain):
        log.info("Last update too recent")
    if chain in NO_BOOST_CHAINS:
        boosts = {"userData": {}}
    else:
        boosts = download_boosts(chain)
    rewards_data = generate_rewards_in_range(
        chain,
        start,
        end,
        save=save,
        past_tree=past_rewards,
        tree_manager=tree_manager,
        boosts=boosts,
    )
    log.info("Generated rewards")

    log.info(
        f"\n==== Proposing root with rootHash {rewards_data['rootHash']} ====\n"
    )
    if env_config.production or env_config.test:
        tx_hash, success = tree_manager.propose_root(rewards_data)
        if success:
            upload_proposed_boosts(boosts, chain)
    return rewards_data


def approve_root(
        chain: str, start: int, end: int, current_rewards: Dict, tree_manager: TreeManager
):
    """Approve latest root on a chain

    :param chain: chain to approve root
    :param start: start block for rewards
    :param end: end block for rewards
    :param current_rewards: past rewards merkle tree
    :param tree_manager: TreeManager object
    """
    if chain in NO_BOOST_CHAINS:
        boosts = {"userData": {}}
    else:
        boosts = download_proposed_boosts(chain)

    rewards_data = generate_rewards_in_range(
        chain,
        start,
        end,
        save=False,
        past_tree=current_rewards,
        tree_manager=tree_manager,
        boosts=boosts,
    )
    if env_config.test or env_config.staging:
        log.info(
            f"\n==== Approving root with rootHash {rewards_data['rootHash']} ====\n"
        )
        boosts = add_multipliers(
            boosts,
            rewards_data["multiplierData"],
            rewards_data["userMultipliers"],
        )
        if chain not in NO_BOOST_CHAINS:
            upload_boosts(boosts, chain)
        return rewards_data
    if tree_manager.matches_pending_hash(rewards_data["rootHash"]):
        log.info(
            f"\n==== Approving root with rootHash {rewards_data['rootHash']} ====\n"
        )

        tx_hash, success = tree_manager.approve_root(rewards_data)
        if success:
            upload_tree(
                rewards_data["fileName"],
                rewards_data["merkleTree"],
                chain,
                staging=env_config.test or env_config.staging,
            )

            boosts = add_multipliers(
                boosts,
                rewards_data["multiplierData"],
                rewards_data["userMultipliers"],
            )
            if chain not in NO_BOOST_CHAINS:
                upload_boosts(boosts, chain, True)
            claimable_rewards_deficits = get_claimable_rewards_deficits(chain, end)

            rewards_info = rewards_data["sett_rewards_analytics"]
            rewards_info["claimable_rewards_deficits"] = json.dumps(
                claimable_rewards_deficits, use_decimal=True
            )
            put_rewards_data(
                chain, tree_manager.next_cycle, start, end,
                rewards_info
            )
            return rewards_data
    else:
        pending_hash = HexBytes(
            tree_manager.badger_tree.pendingMerkleContentHash().call()
        )
        console_and_discord(
            f"Approve hash {rewards_data['rootHash']} "
            f"doesn't match pending hash {pending_hash.hex()}",
            chain,
        )
        return rewards_data


def generate_rewards_in_range(
        chain: str,
        start: int,
        end: int,
        save: bool,
        past_tree: Dict,
        tree_manager: TreeManager,
        boosts: Dict,
):
    """Generate chain rewards for a chain within two blocks

    :param chain: chain to generate rewards
    :param start: start block for rewards
    :param end: end block for rewards
    :param save: flag to save file locally
    :param past_tree: past rewards merkle tree
    :param tree_manager: TreeManager object
    :param boosts: Boost object
    """
    all_schedules, setts = fetch_all_schedules(chain, int(start), int(end))

    console_and_discord(f"Generating rewards for {len(setts)} setts", chain)

    rewards_list = []
    rewards_manager = RewardsManager(
        chain, tree_manager.next_cycle, start, end, boosts["userData"]
    )

    log.info("Calculating Tree Rewards...")
    tree_rewards = rewards_manager.calculate_tree_distributions()
    rewards_list.append(tree_rewards)

    log.info("Calculating Sett Rewards...")
    sett_rewards, sett_rewards_analytics = rewards_manager.calculate_all_sett_rewards(
        setts, all_schedules
    )
    rewards_list.append(sett_rewards)

    new_rewards = combine_rewards(rewards_list, rewards_manager.cycle)

    log.info("Combining cumulative rewards... \n")
    cumulative_rewards = process_cumulative_rewards(past_tree, new_rewards)

    log.info("Converting to merkle tree... \n")
    merkle_tree = tree_manager.convert_to_merkle_tree(cumulative_rewards, start, end)
    root_hash = rewards_manager.web3.keccak(text=merkle_tree["merkleRoot"])
    chain_id = CHAIN_IDS[chain]

    file_name = f"rewards-{chain_id}-{encode_hex(root_hash)}.json"

    verify_rewards(past_tree, merkle_tree, chain)
    if save:
        with open(file_name, "w") as fp:
            json.dump(merkle_tree, fp, indent=4)

    return {
        "merkleTree": merkle_tree,
        "rootHash": root_hash.hex(),
        "fileName": file_name,
        "multiplierData": rewards_manager.get_sett_multipliers(),
        "userMultipliers": rewards_manager.get_user_multipliers(),
        "sett_rewards_analytics": sett_rewards_analytics,
    }
