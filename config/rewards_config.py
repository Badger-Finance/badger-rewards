from helpers.time_utils import hours


class RewardsConfig:
    def __init__(self):
        self.globalStakingStartBlock = 11252068
        self.root_update_intervals = {
            "eth": hours(1),
            "polygon": hours(0.05),
            "arbitrum": hours(0.5),
        }
        self.rootUpdateMinInterval = hours(0.05)
        self.maxStartBlockAge = 3200
        self.debug = False

    def root_update_interval(self, chain):
        return self.root_update_intervals[chain]


rewards_config = RewardsConfig()
