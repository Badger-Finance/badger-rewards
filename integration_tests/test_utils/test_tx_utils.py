from decimal import Decimal
import pytest
from rewards.utils.tx_utils import confirm_transaction, get_gas_price_of_tx, get_transaction
from config.singletons import env_config
from helpers.enums import Network

TEST_NETWORK_INFO = [
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


@pytest.mark.parametrize("network_info", TEST_NETWORK_INFO)
def test_check_tx_receipt(discord_mocker, network_info):
    web3 = env_config.get_web3(network_info["network"])
    assert get_transaction(web3, network_info["valid_tx"], 2, network_info["network"])
    with pytest.raises(Exception):
        get_transaction(
            web3, network_info["invalid_tx"], 2, network_info["network"], tries=0
        )
    assert discord_mocker.called


@pytest.mark.parametrize("network_info", TEST_NETWORK_INFO)
def test_confirm_transaction__happy_path(discord_mocker, network_info):
    web3 = env_config.get_web3(network_info["network"])
    success, __ = confirm_transaction(
        web3, network_info["valid_tx"], network_info["network"]
    )
    assert success


@pytest.mark.parametrize("network_info", TEST_NETWORK_INFO)
def test_get_gas_price_of_tx(discord_mocker, network_info):
    web3 = env_config.get_web3(network_info["network"])
    price = get_gas_price_of_tx(web3, network_info["network"], network_info["valid_tx"])
    assert price != Decimal(0.0)
