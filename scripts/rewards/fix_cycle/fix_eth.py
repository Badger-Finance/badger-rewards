import json

from helpers.enums import Network
from rewards.aws.trees import download_latest_tree
from scripts.rewards.fix_cycle.fix_cycle import fix_cycle

if __name__ == "__main__":
    fix_cycle(Network.Ethereum)
