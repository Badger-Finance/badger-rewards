from scripts.rewards.utils.propose_rewards import propose_rewards
from scripts.rewards.utils.approve_rewards import approve_rewards


def test_propose_approve_rewards(chain):
    propose_rewards(chain)
    rewards_data = approve_rewards(chain)
    print(rewards_data)
