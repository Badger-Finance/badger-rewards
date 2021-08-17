from rewards.classes.UserBalance import UserBalances
from rewards.classes.RewardsList import RewardsList

from rich.console import Console

console = Console()


class TreeManager:
    def __init__(self, chain: str, start: int, end: int):
        self.chain = chain
        self.start = start
        self.end = end
        self.cycle = self.get_current_cycle()
        self.rewardsList = RewardsList(self.cycle)

    def convert_to_merkle_tree(self):
        pass

    def approve_root(self):
        pass

    def propose_root(self):
        pass

    def get_current_cycle(self):
        return 1

    def fetch_current_tree(self):
        pass

    def fetch_past_rewards(self):
        pass
