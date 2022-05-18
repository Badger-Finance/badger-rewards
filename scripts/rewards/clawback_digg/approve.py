from scripts.rewards.utils.custom_cycle import custom_eth_approve
from helpers.enums import Network
from scripts.rewards.clawback_digg.clawback import (
    clawback_func,
    clawback_test
)

if __name__ == "__main__":
    custom_eth_approve(Network.Ethereum, clawback_func, clawback_test)
