from scripts.rewards.utils.custom_cycle import custom_propose
from helpers.enums import Network
from scripts.rewards.retroactive_bribe_processor.retroactive import (
    retroactive_func,
    test_retroactive_func
)

if __name__ == "__main__":
    custom_propose(Network.Ethereum, retroactive_func, test_retroactive_func)
