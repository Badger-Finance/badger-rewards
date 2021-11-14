from tests.utils import set_env_vars

set_env_vars()

from helpers.enums import Network
from rewards_tests.test_propose_approve_rewards import test_propose_approve_rewards

if __name__ == "__main__":
    test_propose_approve_rewards(Network.Polygon)
