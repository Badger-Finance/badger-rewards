from hexbytes import HexBytes
from rewards.aws.trees import upload_tree
from rewards.classes.RewardsManager import RewardsManager
from rewards.classes.TreeManager import TreeManager
from rewards.classes.RewardsList import RewardsList
from rewards.classes.Schedule import Schedule
from rewards.rewards_utils import combine_rewards
from rewards.rewards_checker import verify_rewards
from rewards.aws.boost import add_multipliers, download_boosts
from rewards.aws.helpers import get_secret
from helpers.web3_utils import make_contract
from helpers.constants import DISABLED_VAULTS, EMISSIONS_CONTRACTS
from helpers.discord import send_message_to_discord
from subgraph.queries.setts import list_setts
from typing import List
from rich.console import Console
from config.env_config import env_config
from config.rewards_config import rewards_config
from eth_utils.hexadecimal import encode_hex
from typing import List, Dict
import json

console = Console()


def console_and_discord(msg: str):
    url = get_secret(
        "cycle-bot/prod-discord-url", "DISCORD_WEBHOOK_URL", test=env_config.test
    )
    console.log(msg)
    send_message_to_discord("Rewards Cycle", msg, [], "Rewards Bot", url=url)


def parse_schedules(schedules) -> Dict[str, List[Schedule]]:
    """
    Parse unlock shcedules
    :param schedules: schedules to parse
    """
    schedulesByToken = {}
    console.log("Fetching schedules...")
    for s in schedules:
        schedule = Schedule(s[0], s[1], s[2], s[3], s[4], s[5])
        if schedule.token not in schedulesByToken:
            schedulesByToken[schedule.token] = []
        schedulesByToken[schedule.token].append(schedule)
    return schedulesByToken


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
    console.log("Fetched {} schedules".format(len(all_schedules)))
    return all_schedules, setts_with_schedules


def fetch_setts(chain: str) -> List[str]:
    """
    Fetch setts that are eligible for rewards
    :param chain:
    """
    setts = list_setts(chain)
    filteredSetts = list(filter(lambda x: x not in DISABLED_VAULTS, setts))
    return [env_config.get_web3().toChecksumAddress(s) for s in filteredSetts]


def process_cumulative_rewards(current, new: RewardsList):
    """Combine past rewards with new rewards

    :param current: current rewards
    :param new: new rewards
    :return: [description]
    :rtype: [type]
    """
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


def propose_root(chain: str, start: int, end: int, pastRewards, save=False):
    """
    Propose a root on a chain

    :param chain: chain to propose root
    :param start: start block for rewards
    :param end: end block for rewards
    :param save: flag to save rewards file locally, defaults to False
    :type save: bool, optional
    """
    treeManager = TreeManager(chain)
    currentMerkleData = treeManager.fetch_current_merkle_data()
    w3 = env_config.get_web3(chain)
    currentTime = w3.eth.getBlock(w3.eth.block_number)["timestamp"]
    timeSinceLastUpdate = currentTime - currentMerkleData["lastUpdateTime"]

    if timeSinceLastUpdate < rewards_config.rootUpdateMinInterval:
        console.log("[bold yellow]===== Last update too recent () =====[/bold yellow]")
        #return
    rewards_data = generate_rewards_in_range(
        chain, start, end, save=False, pastTree=pastRewards
    )
    console.log("Generated rewards")

    console.log(
        "\n==== Proposing root with rootHash {} ====\n".format(rewards_data["rootHash"])
    )
    tx_hash, success = treeManager.propose_root(rewards_data)
    # if success:
    #     upload_tree(
    #         rewards_data["fileName"],
    #         rewards_data["merkleTree"],
    #         chain,
    #         staging=env_config.test,
    #     )


def approve_root(chain: str, start: int, end: int, currentRewards):
    """Approve latest root on a chain

    :param chain: chain to approve root
    :param start: start block for rewards
    :param end: end block for rewards
    """
    treeManager = TreeManager(chain)
    console.log(treeManager.has_pending_root())
    if not treeManager.has_pending_root():
        return
    else:
        rewards_data = generate_rewards_in_range(
            chain, start, end, save=False, pastTree=currentRewards
        )
        console.log(
            "\n==== Approving root with rootHash {} ====\n".format(
                rewards_data["rootHash"]
            )
        )
        tx_hash, success = treeManager.approve_root(rewards_data)
        if success:
            add_multipliers(
                rewards_data["multiplierData"], rewards_data["userMultipliers"]
            )
            upload_tree(
                rewards_data["fileName"],
                rewards_data["merkleTree"],
                chain,
                staging=env_config.test,
            )
            return rewards_data


def generate_rewards_in_range(chain: str, start: int, end: int, save: bool, pastTree):
    """Generate chain rewards for a chain within two blocks

    :param chain: chain to generate rewards
    :param start: start block for rewards
    :param end: end block for rewards
    :param save: flag to save file locally
    """
    allSchedules, setts = fetch_all_schedules(chain, fetch_setts(chain))
    
    console_and_discord("Generating rewards for {} setts".format(len(setts)))

    treeManager = TreeManager(chain)

    rewardsManager = RewardsManager(chain, treeManager.nextCycle, start, end)

    console.log("Calculating Tree Rewards...")
    treeRewards = rewardsManager.calculate_tree_distributions()

    console.log("Calculating Sett Rewards...")
    boosts = download_boosts()
    settRewards = rewardsManager.calculate_all_sett_rewards(
        setts, allSchedules, boosts["userData"]
    )
    newRewards = combine_rewards([settRewards, treeRewards], rewardsManager.cycle)

    console.log("Combining cumulative rewards... \n")
    cumulativeRewards = process_cumulative_rewards(pastTree, newRewards)

    console.log("Converting to merkle tree... \n")
    merkleTree = treeManager.convert_to_merkle_tree(cumulativeRewards, start, end)
    rootHash = rewardsManager.web3.keccak(text=merkleTree["merkleRoot"])
    chainId = rewardsManager.web3.eth.chain_id

    fileName = "rewards-{}-{}.json".format(chainId, encode_hex(rootHash))

    verify_rewards(pastTree, merkleTree)

    if save:
        with open(fileName, "w") as fp:
            json.dump(merkleTree, fp)

    return {
        "merkleTree": merkleTree,
        "rootHash": rootHash.hex(),
        "fileName": fileName,
        "multiplierData": rewardsManager.get_sett_multipliers(),
        "userMultipliers": rewardsManager.get_user_multipliers(),
    }
