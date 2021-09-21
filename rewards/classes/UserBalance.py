from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class UserBalance:
    address: str
    balance: int
    token: str

    def boost_balance(self, boost):
        self.balance = self.balance * boost


@dataclass
class UserBalances:
    user_balances: Dict[str, UserBalance] = field(default_factory=lambda: [])
    sett_type: str = field(default="none")
    sett_ratio: int = field(default=0)

    def __post_init__(self):
        if len(self.user_balances) > 0:
            self.user_balances = {u.address: u for u in self.user_balances}
        else:
            self.user_balances = {}

    def total_balance(self):
        return sum([u.balance for u in self.user_balances.values()])

    def percentage_of_total(self, addr):
        return self[addr].balance / self.total_balance()

    def __getitem__(self, key):
        return self.user_balances.get(key, None)

    def __setitem__(self, key, value):
        self.user_balances[key] = value

    def __contains__(self, key):
        return key in self.user_balances

    def __add__(self, other):
        new_user_balances = self.user_balances
        for user in other.user_balances.values():
            if user.address in new_user_balances:
                new_user_balances[user.address].balance += user.balance
            else:
                new_user_balances[user.address] = user
        return UserBalances(new_user_balances.values())

    def __iter__(self):
        for user in self.user_balances.values():
            yield user

    def __len__(self):
        return len(self.user_balances)
