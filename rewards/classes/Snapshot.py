from __future__ import annotations

import json
from decimal import Decimal
from typing import Dict, Tuple, Optional

from rich.console import Console
from web3 import Web3
from badger_api.config import get_api_specific_path
from badger_api.requests import fetch_ppfs, fetch_token_prices
from config.constants.addresses import (
    BAURA_DIGG_WBTC, BDIGG, BSLP_DIGG_WBTC, BUNI_DIGG_WBTC, DIGG, WBTC
)
from helpers.discord import get_discord_url, send_message_to_discord
from helpers.enums import BotType, Network
from rewards.feature_flags.feature_flags import DIGG_BOOST, flags

console = Console()


class Snapshot:
    def __init__(
        self, token, balances, ratio=1, type="none",
        chain: Optional[Network] = Network.Ethereum
    ):
        self.type = type
        self.ratio = Decimal(ratio)
        self.token = Web3.toChecksumAddress(token)
        self.balances = self.parse_balances(balances)
        self.chain = chain

    def __repr__(self) -> str:
        return json.dumps(self.balances, indent=4)

    def parse_balances(self, bals) -> Dict[str, Decimal]:
        new_bals = {}
        for addr, balance in bals.items():
            new_bals[Web3.toChecksumAddress(addr)] = Decimal(str(balance))
        return new_bals

    def total_balance(self) -> Decimal:
        return Decimal(sum(list(self.balances.values())))

    def zero_balance(self, address: str):
        if address in self.balances:
            self.balances[address] = 0

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
        if other is None:
            return self
        for addr, bal in other:
            new_bals[addr] = new_bals.get(addr, 0) + bal

        return Snapshot(self.token, new_bals, self.ratio, self.type)

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)

    def convert_to_usd(
        self, chain: Network, bot_type: BotType = BotType.Boost
    ) -> Snapshot:
        discord_url = get_discord_url(chain, bot_type)
        prices = fetch_token_prices()
        staging_prices = fetch_token_prices(get_api_specific_path("staging"))
        wbtc_price = prices[WBTC]
        digg_price = prices[DIGG]
        if self.token not in prices or prices[self.token] == 0:
            price = Decimal(0)

            # Try to fallback to staging for pricing
            console.log(f"CANT FIND PRODUCTION PRICING FOR {self.token}")
            send_message_to_discord(
                "**ERROR**",
                f"Pricing for {self.token} not in production, checking staging",
                [],
                "Boost Bot",
                url=discord_url,
            )
            if self.token not in staging_prices:
                price = Decimal(0)
                console.log(f"CANT STAGING FIND PRICING FOR {self.token}")
                send_message_to_discord(
                    "**ERROR**",
                    f"{self.token} is not in production or staging pricing",
                    [],
                    "Boost Bot",
                    url=discord_url,
                )
            else:
                price = Decimal(staging_prices[self.token]) * self.ratio
        elif not flags.flag_enabled(DIGG_BOOST):
            price = Decimal(prices[self.token]) * self.ratio
        elif self.token == DIGG:
            price = Decimal(wbtc_price)
        elif self.token == BDIGG:
            _, digg_ppfs = fetch_ppfs()
            price = Decimal(wbtc_price * digg_ppfs)
        elif self.token in [BUNI_DIGG_WBTC, BSLP_DIGG_WBTC, BAURA_DIGG_WBTC]:
            price = Decimal(prices[self.token] * float(self.ratio) * (wbtc_price / digg_price))  # noqa: E501
        else:
            price = Decimal(prices[self.token]) * self.ratio

        new_bals = {}
        for addr, bal in self.balances.items():
            new_bals[addr] = bal * price
        return Snapshot(self.token, new_bals, self.ratio, self.type)
