from rewards.classes.UserBalance import UserBalances


class EmissionsManager:
    def __init__(self, chain, cycle, start, end):
        self.chain = chain
        self.cycle = cycle
        self.start = start
        self.end = end
        self.rewardsList = {}

    def convert_to_merkle_tree(self):
        pass

    def approve_root(self):
        pass

    def propose_root(self):
        pass
