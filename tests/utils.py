import json
import os
from decimal import Decimal

from eth_account import Account
from hexbytes import HexBytes

from helpers.enums import Network
from config.constants.addresses import (
    ARB_BADGER,
    ARB_BSWAPR_WETH_SWAPR,
    BADGER,
    BCVXCRV,
    DIGG,
    POLY_BADGER,
    POLY_SUSHI,
    XSUSHI,
)


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
TEST_WALLET = "0xD27E9195aA35A7dE31513656AD5d4D29268f94eC"
TEST_WALLET_ANOTHER = "0xF9e11762d522ea29Dd78178c9BAf83b7B093aacc"


CLAIMABLE_BALANCES_DATA_ETH = {
    "rewards": {
        TEST_WALLET: [
            {
                "address": BADGER,
                "balance": "148480869281534217908",
            },
            {
                "address": BCVXCRV,
                "balance": "10000000000000",
            },
            {
                "address": XSUSHI,
                "balance": "242132828968734472427025860105531410917",
            },
        ],
        TEST_WALLET_ANOTHER: [
            {
                "address": BADGER,
                "balance": "8202381382803713155",
            },
            {"address": DIGG, "balance": "148480869281534217908"},
            {
                "address": BCVXCRV,
                "balance": "40000000000000",
            },
            {
                "address": XSUSHI,
                "balance": "4169175341925473404499430551565743649791614840189435481041751238508157",
            },
        ],
    },
}

CLAIMABLE_BALANCES_DATA_POLY = {
    "rewards": {
        TEST_WALLET: [
            {
                "address": POLY_BADGER,
                "balance": "148480869281534217908",
            },
            {
                "address": POLY_SUSHI,
                "balance": "2421328289687344724270258601055314109178877723910682205504219578892288",
            },
        ],
        TEST_WALLET_ANOTHER: [
            {
                "address": POLY_BADGER,
                "balance": "8202381382803713155",
            },
            {
                "address": POLY_SUSHI,
                "balance": "2656585570737360069",
            },
        ],
    },
}

CLAIMABLE_BALANCES_DATA_ARB = {
    "rewards": {
        TEST_WALLET: [
            {
                "address": ARB_BADGER,
                "balance": "148480869281534217908",
            },
            {
                "address": ARB_BSWAPR_WETH_SWAPR,
                "balance": "2421328289687344724270258601055314109178877723910682205504219578892288",
            },
        ],
        TEST_WALLET_ANOTHER: [
            {
                "address": ARB_BADGER,
                "balance": "8202381382803713155",
            },
            {
                "address": ARB_BSWAPR_WETH_SWAPR,
                "balance": "2656585570737360069",
            },
        ],
    },
}


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


def mock_get_claimable_data(chain, block):
    print(block, chain)
    if chain == Network.Ethereum:
        return balances_to_data(CLAIMABLE_BALANCES_DATA_ETH)
    elif chain == Network.Arbitrum:
        return balances_to_data(CLAIMABLE_BALANCES_DATA_ARB)
    elif chain == Network.Polygon:
        return balances_to_data(CLAIMABLE_BALANCES_DATA_POLY)


def balances_to_data(bals):
    return [{"address": k, "claimableBalances": v} for k, v in bals["rewards"].items()]
