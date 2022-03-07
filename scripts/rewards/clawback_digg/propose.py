from scripts.rewards.utils.custom_cycle import custom_propose
from helpers.enums import Network
from scripts.rewards.clawback_digg.clawback import (
    clawback_func,
    clawback_test
)

if __name__ == "__main__":
    custom_propose(Network.Ethereum, clawback_func, clawback_test)
