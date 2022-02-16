from helpers.enums import Network
from scripts.rewards.fix_cycle.fix_cycle import fix_cycle


if __name__ == "__main__":
    fix_cycle(Network.Arbitrum)
