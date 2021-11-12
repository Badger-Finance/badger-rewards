import pytest
import logging

from helpers.enums import Network
from tests.utils import set_env_vars
from helpers.enums import Network

set_env_vars()
logger = logging.getLogger("tx-utils")

from rewards.utils.tx_utils import get_transaction
from config.singletons import env_config


@pytest.mark.require_network("hardhat-fork")
def test_check_tx_receipt():
    active_networks = [
        {
            "network": Network.Ethereum,
            "valid_tx": "0xc1d6fb782044679da2af2aa7dc5721b53c9557727d3abc9839aaf10c2bd56454",
            "invalid_tx": "0xc1d6fb782044679da2af2aa7dc5721b53c9557727d3abc9839aaf10c2bd",
        },
        {
            "network": Network.Polygon,
            "valid_tx": "0x01e1ada7c258d624849b257b82a36a28c31eb6ffc5d56d63c9a09740ca45ad2c",
            "invalid_tx": "0x01e1ada7c258d624849b257b82a36a28c31eb6ffc5d56d63c9a0974",
        },
        {
            "network": Network.Arbitrum,
            "valid_tx": "0xb0917c4cd5638a4a4fb0e54a47f785d5e9fd97359e5d1e725440c02c7f54e34a",
            "invalid_tx": "0xb0917c4cd5638a4a4fb0e54a47f785d5e9fd97359e5d1e725440",
        },
    ]
    for network_info in active_networks:
        web3 = env_config.get_web3(network_info["network"])
        logger.info(
            f"Checking to see if valid tx {network_info['valid_tx']} is on the {network_info['network']} network"
        )
        assert get_transaction(
            web3, network_info["valid_tx"], 2, network_info["network"]
        )
        with pytest.raises(Exception):
            get_transaction(
                web3, network_info["invalid_tx"], 2, network_info["network"]
            )
