from decimal import Decimal
from hexbytes import HexBytes
import json
import os
from helpers.enums import Network


def set_env_vars():
    os.environ["ENV"] = "TEST"
    os.environ["KUBE"] = "False"
    os.environ["AWS_SECRET_ACCESS_KEY"] = ""
    os.environ["AWS_ACCESS_KEY_ID"] = ""


def get_mock_json(name):
    file_name = f"tests/mock_files/{name}.json"
    return json.load(open(file_name))


test_address = "0x05995bc5736707208EBDb18BC5bE812668b525B2"
test_key = "0f0bdc830bde4be43c3a54c369c6f6a94ac9071911dc3913e35ce5ed8fe955b9"
chains = [Network.Ethereum, Network.Arbitrum, Network.Polygon]

mock_tree = get_mock_json("mock_tree")
mock_boosts = get_mock_json("mock_boosts")
mock_claimed_for = get_mock_json("mock_claimed_for")
mock_claimable_bals = get_mock_json("mock_claimable_bals")
mock_balances = get_mock_json("mock_balances")
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
