from decimal import Decimal
from helpers.enums import Network
from rewards.classes.RewardsList import RewardsList
from rewards.snapshot.chain_snapshot import sett_snapshot
import config.constants.addresses as addresses
from rewards.utils.rewards_utils import (
    combine_rewards,
    distribute_rewards_from_total_snapshot,
    merkle_tree_to_rewards_list
)


distributions = [
    {
        "sett": addresses.BVECVX,
        "block": 14806809,
        "amount": Decimal("9041178891053935509633"),
        "token": addresses.BADGER
    },
    {
        "sett": addresses.BVECVX,
        "block": 14806809,
        "amount": Decimal("12179126369595468422025 "),
        "token": addresses.BVECVX
    },
    {
        "sett": addresses.BVECVX_CVX_LP_SETT,
        "block": 14806809,
        "amount": Decimal("2009150864678652273513"),
        "token": addresses.BADGER
    }
]


def retroactive_func(tree) -> RewardsList:
    rewards_list = merkle_tree_to_rewards_list(tree)

    retro_rewards = []
    for distro in distributions:
        vault = distro["sett"]
        block = distro["block"]
        amount = distro["amount"]
        snapshot = sett_snapshot(Network.Ethereum, block, vault)
        retro_rewards.append(distribute_rewards_from_total_snapshot(
            int(amount),
            snapshot,
            distro["token"],
            block
        ))
    return combine_rewards([*retro_rewards, rewards_list], 5270)


def test_retroactive_func(old_tree, new_tree):
    token_agg = {}
    for distro in distributions:
        token = distro["token"]
        token_agg[token] = token_agg.get(token, 0) + int(distro["amount"])
    for token, amount in old_tree["tokenTotals"].items():
        if token in [addresses.BVECVX, addresses.BADGER]:
            if not new_tree["tokenTotals"][token] > amount:
                return False
    return True
