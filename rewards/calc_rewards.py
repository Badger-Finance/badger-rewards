from rewards.aws.trees import upload_tree
from toolz.itertoolz import cons
from rewards.classes.RewardsManager import RewardsManager
from rewards.classes.TreeManager import TreeManager
from rewards.classes.RewardsList import RewardsList
from rewards.classes.Schedule import Schedule
from rewards.rewards_utils import combine_rewards

from rewards.aws.boost import download_boosts
from helpers.web3_utils import make_contract
from helpers.constants import DISABLED_VAULTS, REWARDS_LOGGER
from helpers.discord import send_message_to_discord
from subgraph.client import list_setts
from typing import List
from rich.console import Console
from config.env_config import env_config
from config.rewards_config import rewards_config

import json

console = Console()


def console_and_discord(msg):
    console.log(msg)
    send_message_to_discord("Rewards Cycle", msg, [], "Rewards Bot")


def parse_schedules(schedules):
    schedulesByToken = {}
    console.log("Fetching schedules...")
    for s in schedules:
        schedule = Schedule(s[0], s[1], s[2], s[3], s[4], s[5])
        if schedule.token not in schedulesByToken:
            schedulesByToken[schedule.token] = []
        schedulesByToken[schedule.token].append(schedule)
    return schedulesByToken


def fetch_all_schedules(chain, setts: List[str]):
    logger = make_contract(REWARDS_LOGGER[chain], "RewardsLogger", chain)
    allSchedules = {}
    for sett in setts:
        schedules = logger.functions.getAllUnlockSchedulesFor(sett).call()
        allSchedules[sett] = parse_schedules(schedules)
    console.log("Fetched {} schedules".format(len(allSchedules)))
    return allSchedules


def fetch_setts(chain: str):
    """
    Fetch setts that are eligible for rewards

    :param chain:
    """
    setts = list_setts(chain)
    filteredSetts = list(filter(lambda x: x not in DISABLED_VAULTS, setts))
    return [env_config.get_web3().toChecksumAddress(s) for s in filteredSetts]


def process_cumulative_rewards(current, new: RewardsList):
    result = RewardsList(new.cycle)

    # Add new rewards
    for user, claims in new.claims.items():
        for token, claim in claims.items():
            result.increase_user_rewards(user, token, claim)

    # Add existing rewards
    for user, userData in current["claims"].items():
        for i in range(len(userData["tokens"])):
            token = userData["tokens"][i]
            amount = userData["cumulativeAmounts"][i]
            result.increase_user_rewards(user, token, int(amount))

    # result.printState()
    return result


def propose_root(chain, start, end):
    treeManager = TreeManager(chain, start, end)
    pendingMerkleData = treeManager.fetch_pending_merkle_data()
    w3 = env_config.get_web3(chain)
    currentTime = w3.eth.getBlock(w3.eth.block_number)["timestamp"]
    timeSinceLastUpdate = currentTime - pendingMerkleData["lastUpdateTime"]

    if timeSinceLastUpdate < rewards_config.rootUpdateMinInterval:
        console.log(
            "[bold yellow]===== Last update too recent ({}) =====[/bold yellow]"
        )
        return

    rewards_data = generate_rewards_in_range(chain, start, end)
    if not env_config.test:
        treeManager.propose_root(rewards_data)
        upload_tree(rewards_data["fileName"], rewards_data["merkleTree"], publish=True)


def update_root(chain, start, end):
    treeManager = TreeManager(chain, start, end)
    if not treeManager.has_pending_root():
        return
    else:
        rewards_data = generate_rewards_in_range(chain, start, end)
        if not env_config.test:
            treeManager.approve_root(rewards_data)
            upload_tree(rewards_data["fileName"], rewards_data["merkleTree"], chain)


def generate_rewards_in_range(chain: str, start: int, end: int, save=False):
    setts = fetch_setts(chain)
    console_and_discord("Generating rewards for {} setts".format(len(setts)))
    allSchedules = fetch_all_schedules(chain, setts)
    boosts = download_boosts()

    treeManager = TreeManager(chain, start, end)

    rewardsManager = RewardsManager(chain, treeManager.nextCycle, start, end)
    console.log("Calculating Sett Rewards...")

    settRewards = rewardsManager.calculate_all_sett_rewards(
        setts, allSchedules, boosts["userData"]
    )

    pastRewards = treeManager.fetch_current_tree()

    # treeRewards = rewardsManager.calculate_tree_distributions()

    newRewards = combine_rewards([settRewards], rewardsManager.cycle)
    cumulativeRewards = process_cumulative_rewards(pastRewards, newRewards)

    merkleTree = treeManager.convert_to_merkle_tree(cumulativeRewards)
    rootHash = rewardsManager.web3.keccak(text=merkleTree["merkleRoot"])
    fileName = "rewards-1-{}.json".format(rootHash)
    verify_rewards(pastRewards, merkleTree)

    if save:
        with open(fileName, "w") as fp:
            json.dumps(merkleTree, fp)

    return {"merkleTree": merkleTree, "rootHash": rootHash, "fileName": fileName}


def verify_rewards(pastRewards, merkleTree):
    return True
