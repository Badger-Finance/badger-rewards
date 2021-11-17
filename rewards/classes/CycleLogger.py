import dataclasses

from rewards.aws.analytics import upload_analytics, upload_schedules
from rewards.classes.Schedule import Schedule


class CycleLogger:
    def __init__(self):
        self.sett_data = {}
        self.tree_distributions = {}
        self.user_data = {}
        self.schedules = {}

        self.start_block = 0
        self.end_block = 0
        self.merkle_root = ""
        self.content_hash = ""

    def set_start_block(self, start):
        self.start_block = start

    def set_end_block(self, end):
        self.end_block = end

    def set_merkle_root(self, merkle_root):
        self.merkle_root = merkle_root

    def set_content_hash(self, content_hash):
        self.content_hash = content_hash

    def add_sett_token_data(self, sett: str, token: str, amount: int):
        if sett not in self.sett_data:
            self.sett_data[sett] = {}
        if token not in self.sett_data[sett]:
            self.sett_data[sett][token] = 0
        self.sett_data[sett][token] += amount

    def add_tree_distribution(self, sett: str, distribution):
        if sett not in self.tree_distributions:
            self.tree_distributions[sett] = []
        self.tree_distributions[sett].append(distribution)

    def add_schedule(self, sett: str, schedule: Schedule):
        if sett not in self.schedules:
            self.schedules[sett] = []
        self.schedules[sett].append(dataclasses.asdict(schedule))

    def save(self, cycle: int, chain: str):
        upload_schedules(chain, self.schedules)
        analytics_data = (
            {
                "cycle": cycle,
                "chain": chain,
                "startBlock": self.start_block,
                "endBlock": self.end_block,
                "merkleRoot": self.merkle_root,
                "contentHash": self.content_hash,
                "totalTokenDist": self.sett_data,
                "treeDistributions": self.tree_distributions,
            },
        )
        upload_analytics(chain, cycle, analytics_data)


cycle_logger = CycleLogger()
