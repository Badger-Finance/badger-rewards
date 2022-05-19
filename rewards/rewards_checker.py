import json
from typing import Dict
from typing import List, Optional, Tuple

from rich.console import Console
from tabulate import tabulate

from badger_api.requests import fetch_token
from config.constants.chain_mappings import TOKENS_TO_CHECK
from helpers.digg_utils import DiggUtils
from helpers.discord import (
    get_discord_url,
    send_code_block_to_discord,
    send_error_to_discord,
)
from helpers.enums import BotType, Network
from rewards.snapshot.claims_snapshot import claims_snapshot

console = Console()


def assert_claims_increase(past_tree: Dict, new_tree: Dict):
    # Each users cumulative claims must only increase
    past_claims = past_tree["claims"]
    new_claims = new_tree["claims"]

    for user, past_claim in past_claims.items():
        if user in new_claims:
            new_claim = new_claims[user]
            for past_token in past_claim["tokens"]:
                past_cumulative_amounts = past_claim["cumulativeAmounts"]
                new_cumulative_amounts = new_claim["cumulativeAmounts"]
                past_amount = past_cumulative_amounts[
                    past_claim["tokens"].index(past_token)
                ]
                new_amount = new_cumulative_amounts[
                    new_claim["tokens"].index(past_token)
                ]
                diff = new_amount - past_amount
                assert diff >= 0


def val(amount, decimals=18):
    return f"{amount / 10 ** decimals:,.18f}"


def token_diff_table_item(
    name: str, before: float, after: float, decimals: Optional[int] = 18
) -> Tuple[float, List]:
    diff = after - before
    console.print(f"Diff for {name} \n")
    table_item = [
        name,
        val(before, decimals=decimals),
        val(after, decimals=decimals),
        val(diff, decimals=decimals),
    ]
    return diff, table_item


def verify_rewards(past_tree, new_tree, chain: Network):
    digg_utils = DiggUtils()
    console.log("Verifying Rewards ... \n")
    claim_snapshot = claims_snapshot(chain, block=int(new_tree["endBlock"]))
    negative_claimable = []
    for token, snapshot in claim_snapshot.items():
        for addr, amount in snapshot:
            if amount < 0:
                if addr not in negative_claimable:
                    negative_claimable[addr] = {}
                negative_claimable[addr][token] = amount
    try:
        assert len(negative_claimable) == 0
    except AssertionError as e:
        send_error_to_discord(
            e,
            f"Negative Claimable \n ```{json.dumps(negative_claimable,indent=4)}```",
            "Negative Rewards Error",
            chain,
        )
        raise e
    table = []
    for name, token in TOKENS_TO_CHECK[chain].items():
        total_before_token = int(past_tree["tokenTotals"].get(token, 0))
        total_after_token = int(new_tree["tokenTotals"].get(token, 0))
        token_info = fetch_token(chain, token)
        decimals = token_info.get("decimals", 18)
        console.log(name, total_before_token, total_after_token)
        if name == "Digg":
            total_before_token = digg_utils.shares_to_fragments(total_before_token)
            total_after_token = digg_utils.shares_to_fragments(total_after_token)
        diff, table_item = token_diff_table_item(
            name, total_before_token, total_after_token, decimals
        )
        table.append(table_item)
    send_code_block_to_discord(
        msg=tabulate(table, headers=["token", "before", "after", "diff"]),
        username="Rewards Bot", url=get_discord_url(chain, BotType.Cycle)
    )
