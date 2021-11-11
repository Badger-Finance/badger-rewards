from scripts.rewards.fix_checksum.fix_checksum import fix_checksum
from helpers.enums import Network

if __name__ == "__main__":
    fix_checksum(Network.Polygon)
