from helpers.enums import Network
from helpers.time_utils import hours


class RewardsConfig:
    def __init__(self):
        self.globalStakingStartBlock = 11252068
        self.root_update_intervals = {
            Network.Ethereum: hours(1.5),
            Network.Polygon: hours(0.05),
            Network.Arbitrum: hours(1.5),
        }
        self.maxStartBlockAge = 3200
        self.debug = False

    def root_update_interval(self, chain):
        return self.root_update_intervals[chain]


rewards_config = RewardsConfig()
