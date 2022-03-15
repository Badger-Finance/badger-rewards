from scripts.rewards.utils.custom_cycle import custom_propose
from helpers.enums import Network
from scripts.rewards.migrate_rewards.migrate import (
    migrate_func,
    migrate_test
)


if __name__ == "__main__":
    custom_propose(Network.Ethereum, migrate_func, migrate_test)
