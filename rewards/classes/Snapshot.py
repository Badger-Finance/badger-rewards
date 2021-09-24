from __future__ import annotations
from typing import Tuple, Dict
from config.env_config import env_config
from badger_api.prices import fetch_token_prices
from helpers.discord import send_message_to_discord


class Snapshot:
    def __init__(self, token, balances, ratio=1, type="none"):
        self.type = type
        self.ratio = ratio
        self.token = token
        self.balances = self.parse_balances(balances)

    def parse_balances(self, bals) -> Dict[str, float]:
        new_bals = {}
        for addr, balance in bals.items():
            new_bals[env_config.get_web3().toChecksumAddress(addr)] = balance
        return new_bals

    def total_balance(self) -> float:
        return sum([u.balance for u in self.balances.values()])

    def boost_balance(self, user, multiple):
        self.balances[user] = self.balances[user] * multiple

    def percentage_of_total(self, addr) -> float:
        addr = env_config.get_web3().toChecksumAddress(addr)
        return self.balances[addr] / self.total_balance()

    def __iter__(self) -> Tuple[str, float]:
        for user, balance in self.balances.items():
            yield user, balance

    def __len__(self) -> int:
        return len(self.balances)

    def __add__(self, other: Snapshot) -> Snapshot:
        new_bals = self.balances.copy()
        for addr, bal in other:
            new_bals[addr] = new_bals.get(addr, 0) + bal

        return Snapshot(self.token, new_bals, self.ratio, self.type)

    def convert_to_usd(self) -> Snapshot:
        prices = fetch_token_prices()
        if self.token not in prices:
            price = 0
            send_message_to_discord(
                "**ERROR**",
                f"Cannot find pricing for {self.token}",
                [],
                "Boost Bot",
            )
        else:
            price = prices[self.token] * self.ratio

        new_bals = {}
        for addr, bal in self.balances.items():
            new_bals[addr] = bal * price

        return Snapshot(self.token, new_bals, self.ratio, self.type)
