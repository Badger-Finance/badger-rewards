from decimal import Decimal
from hexbytes import HexBytes
import json


def get_mock_json(name):
    file_name = f"tests/mock_files/{name}.json"
    return json.load(open(file_name))


test_address = "0xD88a9aF149366d57aEbc32D2eABAdf93EdA41A84"
test_key = "0f0bdc830bde4be43c3a54c369c6f6a94ac9071911dc3913e35ce5ed8fe955b9"
chains = ["eth", "arbitrum", "polygon"]

mock_tree = get_mock_json("mock_tree")
mock_boosts = get_mock_json("mock_boosts")
test_start = int(mock_tree["startBlock"])
test_end = int(mock_tree["endBlock"])
test_cycle = int(mock_tree["cycle"])


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
