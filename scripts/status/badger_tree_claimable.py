from rewards.meta_rewards.unclaimed_rewards import get_unclaimed_rewards
from rich.console import Console
from rewards.aws_utils import download_latest_tree
import json

console = Console()

DFD = "0x20c36f062a31865bED8a5B1e512D9a1A20AA333A"


def find_element_in_list(element, list_element):
    try:
        index_element = list_element.index(element)
        return index_element
    except ValueError:
        return None


def main():
    latest_tree = json.loads(download_latest_tree())

    dfdTotal = latest_tree["tokenTotals"][DFD]

    claims = latest_tree["claims"]
    console.log("DFD tokenTotals: {}".format(dfdTotal))
    calculatedDfdTotal = 0
    for addr, claimData in claims.items():
        tokensIndex = find_element_in_list(DFD, list(claimData["tokens"]))
        if tokensIndex:
            tokenAmount = claimData["cumulativeAmounts"][tokensIndex]
            calculatedDfdTotal += int(tokenAmount)

    console.log(
        "Total : {} vs Calculated Total : {}".format(
            dfdTotal / 1e18, calculatedDfdTotal / 1e18
        )
    )

    claims_addresses = list(claims.keys())
    unclaimed_dfd = get_unclaimed_rewards(claims_addresses)["dfd"]
    unclaimed_dfd_total = sum(unclaimed_dfd.values())
    console.log("Total unclaimed DFD: {}".format(unclaimed_dfd_total))
    console.log("Total unclaimed DFD Wei : {}".format(unclaimed_dfd_total / 1e18))
