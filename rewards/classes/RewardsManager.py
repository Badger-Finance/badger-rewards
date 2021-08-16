from rewards.snapshot.utils import chain_snapshot, sett_snapshot
from subgraph.client import fetch_tree_distributions


class RewardsManager:
    def __init__(self, chain, boosts):
        self.chain = chain
        self.settBalances = {}
        self.boosts = boosts
        self.apyBoosts = {}

    def fetch_sett_snapshot(self, block, sett):
        return sett_snapshot(self.chain, block, sett)

    def calculate_sett_rewards(self, schedules):
        pass

    def boost_balances(self):
        for sett, snapshot in self.settBalances:
            if snapshot.settType == "nonNative":
                preBoost = {}
                for user in snapshot:
                    preBoost[user.address] = snapshot.percentage_of_total(user.address)

                for user in snapshot:
                    boostInfo = self.boosts.get(user)
                    boost = boostInfo.get("boost", 1)
                    user.boost_balance(boost)

                for user in snapshot:
                    postBoost = snapshot.percentage_of_total(user.address)
                    if sett not in self.apyBoosts:
                        self.apyBoosts[sett] = {}

                    self.apyBoosts[sett][user.address] = (
                        postBoost / preBoost[user.address]
                    )

    def calculate_tree_distributions(self, start, end):
        treeDistributions = fetch_tree_distributions(start, end)
        rewards = RewardsList()
        for dist in treeDistributions:
            block = dist["blockNumber"]
            token = dist["token"]["id"]
            strategy = dist["id"].split("-")[0]
            sett = get_sett_from_strategy(strategy)
            balances = sett_snapshot(self, block, sett)
            amount = int(dist["amount"])
            rewardsUnit = amount / sum([u.balance for u in balances])
            for user in balances:
                userRewards = rewardsUnit * user.balance
                rewards.increase_user_rewards(
                    web3.toChecksumAddress(user.address),
                    web3.toChecksumAddress(token),
                    int(userRewards),
                )
        return rewards

    def calc_sushi_distributions(self, start, end):
        pass
