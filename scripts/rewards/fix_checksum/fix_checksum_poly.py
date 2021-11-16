from helpers.enums import Network
from scripts.rewards.fix_checksum.fix_checksum import fix_checksum

if __name__ == "__main__":
    fix_checksum(Network.Polygon)
