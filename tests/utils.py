from brownie import Contract
from decimal import Decimal
from hexbytes import HexBytes
import json

test_address = "0xD88a9aF149366d57aEbc32D2eABAdf93EdA41A84"
test_key = "0f0bdc830bde4be43c3a54c369c6f6a94ac9071911dc3913e35ce5ed8fe955b9"
chains = ["eth", "arbitrum", "polygon"]
with open("./tests/mock_tree.json") as f:
    mock_tree = json.load(f)


def mock_send_discord(
    tx_hash: HexBytes,
    tx_type: str,
    gas_cost: Decimal = None,
    amt: Decimal = None,
    sett_name: str = None,
    chain: str = "ETH",
    url: str = None,
):
    print("sent")
