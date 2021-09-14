from rewards.classes.Schedule import Schedule
from rewards.aws.analytics import upload_analytics
from rewards.aws.analytics import upload_schedules


class CycleLogger:
    def __init__(self):
        self.sett_data = {}
        self.tree_distributions = {}
        self.user_data = {}
        self.schedules = {}

        self.start_block = 0
        self.end_block = 0
        self.root_hash = ""
        self.content_hash = ""

    def set_start_block(self, start):
        self.start = start

    def set_end_block(self, end):
        self.end = end

    def set_root_hash(self, root_hash):
        self.root_hash = root_hash

    def set_content_hash(self, content_hash):
        self.content_hash = content_hash

    def add_sett_data(self, sett: str, token: str, amount: int):
        if sett not in self.sett_data:
            self.sett_data[sett] = {}
        self.sett_data[sett][token] = amount

    def add_tree_distribution(self, sett: str, distribution):
        if sett not in self.tree_distributions:
            self.tree_distributions = []
        self.tree_distributions[sett].append(distribution)

    def add_schedules(self, sett: str, schedule: Schedule):
        if sett not in self.schedules:
            self.schedules = []
        self.tree_distributions[sett].append(schedule.asdict())

    def save(self, cycle: int, chain: str):
        upload_schedules(chain, self.schedules)
        upload_analytics(
            cycle,
            chain,
            {
                "sett_data": self.sett_data,
                "tree_distributions": self.tree_distributions,
            },
        )


cycle_logger = CycleLogger()
