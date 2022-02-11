from scripts.rewards.utils.custom_cycle import custom_propose
from helpers.enums import Network
from scripts.rewards.move_bvecvx import move_bvecvx
if __name__ == "__main__":
    custom_propose(Network.Ethereum, move_bvecvx)


