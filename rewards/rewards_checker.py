from rewards.classes.TreeManager import TreeManager
from rewards.snapshot.claims_snapshot import claims_snapshot
from tabulate import tabulate
from rich.console import Console
from config.env_config import env_config
from helpers.constants import SANITY_TOKEN_AMOUNT, TOKENS_TO_CHECK
from helpers.discord import send_code_block_to_discord, send_error_to_discord
from helpers.digg_utils import digg_utils
import json

console = Console()


def assert_claims_increase(past_tree, new_tree):
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


def token_diff_table(name, before, after, decimals=18):
    diff = after - before
    console.print(f"Diff for {name} \n")
    table = []
    table.append([f"{name} before", val(before, decimals=decimals)])
    table.append([f"{name} after", val(after, decimals=decimals)])
    table.append([f"{name} diff", val(diff, decimals=decimals)])
    return diff, tabulate(table, headers=["token", "amount"])


def verify_rewards(past_tree, new_tree, tree_manager: TreeManager, chain: str):
    console.log("Verifying Rewards ... \n")
    claim_snapshot = claims_snapshot(chain)
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
        )
        raise e

    for name, token in TOKENS_TO_CHECK[chain].items():
        total_before_token = int(past_tree["tokenTotals"].get(token, 0))
        total_after_token = int(new_tree["tokenTotals"].get(token, 0))
        console.log(name, total_before_token, total_after_token)
        if name == "Digg":
            diff, table = token_diff_table(
                name,
                digg_utils.shares_to_fragments(total_before_token),
                digg_utils.shares_to_fragments(total_after_token),
                decimals=9,
            )
            print(
                digg_utils.shares_to_fragments(total_before_token),
                digg_utils.shares_to_fragments(total_after_token),
            )
        else:
            diff, table = token_diff_table(name, total_before_token, total_after_token)
        if not env_config.retroactive:
            try:
                assert diff < SANITY_TOKEN_AMOUNT
            except AssertionError as e:
                send_error_to_discord(e, "Error verifying rewards", "Rewards Error")
                raise e

        send_code_block_to_discord(
            msg=table,
            username="Rewards Bot",
        )
