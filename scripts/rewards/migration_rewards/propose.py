from scripts.rewards.utils.custom_cycle import custom_propose
from helpers.enums impot Network.Ethereum
from scripts.rewards.migration_rewards.migration import migration_rewards
if __name__ == "__main__":
    custom_propose(Network.Ethereum, migration_rewards)

