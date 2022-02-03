from scripts.rewards.utils.custom_cycle import custom_eth_approve
from helpers.enums import Network
from scripts.rewards.migration_rewards.migration import migration_rewards
if __name__ == "__main__":
    custom_eth_approve(Network.Ethereum, migration_rewards)

