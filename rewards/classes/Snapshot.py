from __future__ import annotations

import json
from decimal import Decimal
from typing import Dict, Tuple

from rich.console import Console
from web3 import Web3

from badger_api.requests import fetch_token_prices
from config.singletons import env_config
from helpers.discord import get_discord_url, send_message_to_discord
from helpers.enums import BotType, Network

console = Console()


class Snapshot:
    def __init__(self, token, balances, ratio=1, type="none"):
        self.type = type
        self.ratio = Decimal(ratio)
        self.token = Web3.toChecksumAddress(token)
        self.balances = self.parse_balances(balances)

    def __repr__(self) -> str:
        return json.dumps(self.balances, indent=4)

    def parse_balances(self, bals) -> Dict[str, Decimal]:
        new_bals = {}
        for addr, balance in bals.items():
            new_bals[Web3.toChecksumAddress(addr)] = Decimal(str(balance))
        return new_bals

    def total_balance(self) -> Decimal:
        return Decimal(sum(list(self.balances.values())))

    def boost_balance(self, user, multiple):
        self.balances[user] = self.balances[user] * multiple

    def percentage_of_total(self, addr) -> Decimal:
        addr = Web3.toChecksumAddress(addr)
        return self.balances[addr] / self.total_balance()

    def __iter__(self) -> Tuple[str, Decimal]:
        for user, balance in self.balances.items():
            yield user, balance

    def __len__(self) -> int:
        return len(self.balances)

    def __add__(self, other: Snapshot) -> Snapshot:
        new_bals = self.balances.copy()
        if other == None:
            return self
        for addr, bal in other:
            new_bals[addr] = new_bals.get(addr, 0) + bal

        return Snapshot(self.token, new_bals, self.ratio, self.type)

    def convert_to_usd(
        self, chain: Network, bot_type: BotType = BotType.Boost
    ) -> Snapshot:
        discord_url = get_discord_url(chain, bot_type)
        prices = fetch_token_prices()
        if self.token not in prices:
            price = Decimal(0)
            console.log(f"CANT FIND PRICING FOR {self.token}")
            send_message_to_discord(
                "**ERROR**",
                f"Cannot find pricing for {self.token}",
                [],
                "Boost Bot",
                url=discord_url,
            )
        else:
            price = Decimal(prices[self.token]) * self.ratio

        new_bals = {}
        for addr, bal in self.balances.items():
            new_bals[addr] = bal * price
        return Snapshot(self.token, new_bals, self.ratio, self.type)
