from scripts.rewards.utils.custom_cycle import custom_eth_approve
from helpers.enums import Network
from scripts.rewards.retroactive_multisig_rewards.retroactive import (
    retroactive_func,
    test_retroactive_func
)


if __name__ == "__main__":
    custom_eth_approve(Network.Ethereum, retroactive_func, test_retroactive_func)
