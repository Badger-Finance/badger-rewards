import pytest
import json
import os
from eth_account import Account
from brownie import web3

os.environ["TEST"] = "True"
os.environ["KUBE"] = "False"

from rewards.tx_utils import is_transaction_found


@pytest.mark.require_network("hardhat-fork")
def test_check_tx_receipt():
    valid_tx_hash = "0xc1d6fb782044679da2af2aa7dc5721b53c9557727d3abc9839aaf10c2bd56454"
    invalid_tx_hash = "0xc1d6fb782044679da2af2aa7dc5721b53c9557727d3abc9839aaf10c2bd"

    assert is_transaction_found(web3, valid_tx_hash, 2)
    with pytest.raises(Exception):
        is_transaction_found(web3, invalid_tx_hash, 2)
