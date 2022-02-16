import json
import os
from decimal import Decimal

from eth_account import Account
from hexbytes import HexBytes

from helpers.enums import Network


def set_env_vars():
    os.environ["ENV"] = "TEST"
    os.environ["KUBE"] = "False"
    os.environ["AWS_SECRET_ACCESS_KEY"] = ""
    os.environ["AWS_ACCESS_KEY_ID"] = ""


def get_mock_json(name):
    file_name = f"tests/mock_files/{name}.json"
    return json.load(open(file_name))


test_key = "0f0bdc830bde4be43c3a54c369c6f6a94ac9071911dc3913e35ce5ed8fe955b9"
test_account = Account.from_key(test_key)
test_address = test_account.address
chains = [Network.Ethereum, Network.Arbitrum, Network.Polygon]

mock_tree = get_mock_json("mock_tree")
mock_boosts = get_mock_json("mock_boosts")
mock_boosts_split = get_mock_json("mock_boosts_split")
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


def mock_send_message_to_discord_stg(
    title: str, description: str, fields: list, username: str, url: str = ""
):
    print(description)
    assert "s3://badger-staging-merkle-proofs/" in description
    assert "s3://badger-merkle-proofs/" not in description


def mock_send_message_to_discord_prod(
    title: str, description: str, fields: list, username: str, url: str = ""
):
    print(description)
    assert "s3://badger-staging-merkle-proofs/" not in description
    assert "s3://badger-merkle-proofs/" in description


def mock_send_code_block_to_discord(msg: str, username: str, url: str = None):
    print(msg)
