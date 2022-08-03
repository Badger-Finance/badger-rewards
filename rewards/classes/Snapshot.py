from __future__ import annotations

import json
from decimal import Decimal
from typing import Dict, Tuple, Optional

from rich.console import Console
from web3 import Web3
from badger_api.config import get_api_specific_path
from badger_api.requests import fetch_ppfs, fetch_token_prices
from config.constants.addresses import (
    BAURA_DIGG_WBTC,
    BDIGG,
    BSLP_DIGG_WBTC,
    BUNI_DIGG_WBTC,
    DIGG,
    WBTC,
)
from helpers.discord import get_discord_url, send_message_to_discord
from helpers.enums import Network
from rewards.feature_flags.feature_flags import DIGG_BOOST, flags

console = Console()


class Snapshot:
    def __init__(
        self,
        token,
        balances,
        ratio=1,
        type="none",
        chain: Optional[Network] = Network.Ethereum,
    ):
        self.type = type
        self.ratio = Decimal(str(ratio))
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

    def convert_to_usd(self, chain: Network) -> Snapshot:
        """Converts token prices to USD. Special case is for boosted LP tokens and Digg.
        LP tokens that count towards boost will return the USD amount that counts towards boost.

        Ex 1. Badger/WBTC bSLP is $10k per token. Token counts 50% towards boost (just Badger half).
        Calculated USD value is $5k.

        Ex 2. 40/40/20 Digg/WBTC/graviAURA bSLP is $10k per token. Token counts 40% towards boost
        (just Digg portion). Digg is trading at half the price of BTC (and priced as price of BTC in boost).
        Calculated USD value is $8k. ($10k * .4 * 2 BTC / 1 DIGG)

        Args:
            chain (Network): Blockchain identifier

        Returns:
            Snapshot: Snapshot with updated USD balances
        """
        discord_url = get_discord_url(chain)
        prices = fetch_token_prices(chain)
        staging_prices = fetch_token_prices(chain, get_api_specific_path("staging"))
        wbtc_price = Decimal(0)
        digg_price = Decimal(0)
        if chain == Network.Ethereum:
            wbtc_price = Decimal(prices[WBTC])
            digg_price = Decimal(prices[DIGG])
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
            digg_lp_price = Decimal(prices[self.token])
            price = digg_lp_price * self.ratio * wbtc_price / digg_price  # noqa: E501
        else:
            price = Decimal(prices[self.token]) * self.ratio

        new_bals = {}
        for addr, bal in self.balances.items():
            new_bals[addr] = bal * price
        return Snapshot(self.token, new_bals, self.ratio, self.type)
