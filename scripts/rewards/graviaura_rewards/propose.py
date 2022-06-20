from scripts.rewards.graviaura_rewards.graviaura import graviaura, graviaura_test
from scripts.rewards.utils.custom_cycle import custom_propose
from helpers.enums import Network

if __name__ == "__main__":
    custom_propose(Network.Ethereum, graviaura, graviaura_test)
