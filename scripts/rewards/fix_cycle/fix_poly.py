from scripts.rewards.fix_cycle.fix_cycle import fix_cycle
from helpers.enums import Network

if __name__ == "__main__":
    fix_cycle(Network.Polygon)
