from scripts.rewards.digg_rewards.digg import digg, digg_test
from scripts.rewards.utils.custom_cycle import custom_propose
from helpers.enums import Network

if __name__ == "__main__":
    custom_propose(Network.Ethereum, digg, digg_test)
