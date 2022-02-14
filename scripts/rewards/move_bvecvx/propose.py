from scripts.rewards.utils.custom_cycle import custom_propose
from helpers.enums import Network
from scripts.rewards.move_bvecvx.move_bvecvx import move_bvecvx_func, move_bvecvx_test
if __name__ == "__main__":
    custom_propose(Network.Ethereum, move_bvecvx_func, move_bvecvx_test)


