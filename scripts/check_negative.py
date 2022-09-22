import json
import sys

from helpers.enums import Network
from logging_utils.logger import exception_logging

sys.excepthook = exception_logging


if __name__ == "__main__":
    chain = Network.Ethereum
    diff_data = json.load(open("diff_data.json"))
    sum_negative = {}
    for user, token_data in diff_data["userTokenDiffs"].items():
        for token, amount in token_data.items():
            if amount < 0:
                if token in sum_negative:
                    sum_negative[token] += amount
                else:
                    sum_negative[token] = amount

    with open("negative_balances.json", "w") as fp2:
        json.dump(sum_negative, fp2)
