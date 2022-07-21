from helpers.enums import Network
from helpers.time_utils import hours_to_seconds


class RewardsConfig:
    def __init__(self):
        self.globalStakingStartBlock = 11252068
        self.root_update_intervals = {
            Network.Ethereum: hours_to_seconds(1.5),
            Network.Polygon: hours_to_seconds(0.05),
            Network.Arbitrum: hours_to_seconds(1.5),
            Network.Fantom: hours_to_seconds(1.5)
        }
        self.maxStartBlockAge = 3200
        self.debug = False

    def root_update_interval(self, chain):
        return self.root_update_intervals[chain]


rewards_config = RewardsConfig()
