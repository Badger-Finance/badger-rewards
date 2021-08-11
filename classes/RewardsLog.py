from rich.console import Console
from dataclasses import asdict

console = Console()


class RewardsLog:
    def __init__(self):
        self._totalTokenDist = {}
        self._merkleRoot = ""
        self._contentHash = ""
        self._startBlock = 0
        self._endBlock = 0
        self._unlockSchedules = {}

    def set_merkle_root(self, root):
        self._merkleRoot = root

    def set_content_hash(self, content_hash):
        self._contentHash = content_hash

    def set_start_block(self, startBlock):
        self._startBlock = startBlock

    def set_end_block(self, endBlock):
        self._endBlock = endBlock

    def add_total_token_dist(self, name, token, amount):
        if name not in self._totalTokenDist:
            self._totalTokenDist[name] = {}
        if token not in self._totalTokenDist[name]:
            self._totalTokenDist[name][token] = 0
        self._totalTokenDist[name][token] += amount

    def add_unlock_schedules(self, name, schedule):
        if name not in self._unlockSchedules:
            self._unlockSchedules[name] = []
        self._unlockSchedules[name].append(schedule)

    def add_schedules_in_range(self, name, schedulesByToken, startTime, endTime):
        for token, schedules in schedulesByToken.items():
            for s in schedules:
                if s.endTime > startTime:
                    self.add_unlock_schedules(name, asdict(s))


rewardsLog = RewardsLog()
