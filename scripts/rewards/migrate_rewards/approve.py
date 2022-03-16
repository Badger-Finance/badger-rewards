from scripts.rewards.utils.custom_cycle import custom_eth_approve
from helpers.enums import Network
from scripts.rewards.migrate_rewards.migrate import (
    migrate_func,
    migrate_test
)


if __name__ == "__main__":
    custom_eth_approve(Network.Ethereum, migrate_func, migrate_test)
