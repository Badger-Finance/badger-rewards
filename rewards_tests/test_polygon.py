from tests.utils import set_env_vars

set_env_vars()

from rewards_tests.test_propose_approve_rewards import test_propose_approve_rewards
from helpers.enums import Network

if __name__ == "__main__":
    test_propose_approve_rewards(Network.Polygon)
