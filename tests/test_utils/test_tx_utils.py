from decimal import Decimal
from unittest.mock import MagicMock

import pytest
import responses

from config.constants import GAS_BUFFER
from helpers.enums import Network
from rewards.utils.tx_utils import (
    confirm_transaction,
    get_effective_gas_price,
    get_gas_price_of_tx,
    get_latest_base_fee,
    get_priority_fee,
)
from tests.utils import set_env_vars

set_env_vars()

from config.singletons import env_config
from rewards.utils.tx_utils import get_transaction


@pytest.fixture
def discord_mocker(mocker):
    return mocker.patch("rewards.utils.tx_utils.send_message_to_discord")


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
def test_get_gas_price_of_tx(discord_mocker, network_info):
    web3 = env_config.get_web3(network_info["network"])
    price = get_gas_price_of_tx(web3, network_info["network"], network_info["valid_tx"])
    assert price != Decimal(0.0)


@pytest.mark.parametrize("network_info", TEST_NETWORK_INFO)
def test_get_gas_price_of_tx__invalid_tx(discord_mocker, network_info):
    web3 = MagicMock(
        eth=MagicMock(wait_for_transaction_receipt=MagicMock(side_effect=Exception))
    )
    with pytest.raises(Exception):
        get_gas_price_of_tx(
            web3,
            network_info["network"],
            network_info["invalid_tx"],
            retries_on_failure=1,
        )


@pytest.mark.parametrize("network_info", TEST_NETWORK_INFO)
def test_confirm_transaction__happy_path(discord_mocker, network_info):
    web3 = env_config.get_web3(network_info["network"])
    success, __ = confirm_transaction(
        web3, network_info["valid_tx"], network_info["network"]
    )
    assert success


@pytest.mark.parametrize("network_info", TEST_NETWORK_INFO)
def test_confirm_transaction__unhappy_path(discord_mocker, network_info):
    web3 = MagicMock(
        eth=MagicMock(wait_for_transaction_receipt=MagicMock(side_effect=Exception))
    )
    success, __ = confirm_transaction(
        web3,
        network_info["invalid_tx"],
        network_info["network"],
        retries_on_failure=1,
    )
    assert not success


def test_get_priority_fee():
    reward = 11e9
    web3 = MagicMock(
        eth=MagicMock(fee_history=MagicMock(return_value={"reward": [[reward]]}))
    )
    assert get_priority_fee(web3) == reward / 1


@pytest.mark.parametrize("fee", [1000000, "0x174876e800"])
def test_get_latest_base_fee(fee):
    web3 = MagicMock(
        eth=MagicMock(get_block=MagicMock(return_value={"baseFeePerGas": fee}))
    )
    if type(fee) == str and fee.startswith("0x"):
        fee = int(fee, 0)
    assert get_latest_base_fee(web3) == int(fee)


def test_get_effective_gas_price__eth():
    reward = 11e9
    base_fee = 1000000
    web3 = MagicMock(
        eth=MagicMock(
            get_block=MagicMock(return_value={"baseFeePerGas": base_fee}),
            fee_history=MagicMock(return_value={"reward": [[reward]]}),
        ),
    )
    gas = get_effective_gas_price(web3, Network.Ethereum)
    assert gas == 2 * base_fee + reward


@responses.activate
def test_get_effective_gas_price__polygon_happy(mock_discord):
    web3 = env_config.get_web3(Network.Polygon)
    fast_gas = 125
    responses.add(
        responses.GET,
        "https://gasstation-mainnet.matic.network",
        json={"fast": fast_gas},
        status=200,
    )
    gas = get_effective_gas_price(web3, Network.Polygon)
    assert gas == web3.toWei(int(fast_gas * 1.1), "gwei")


@responses.activate
def test_get_effective_gas_price__polygon_unhappy(mock_discord):
    web3 = env_config.get_web3(Network.Polygon)
    responses.add(
        responses.GET, "https://gasstation-mainnet.matic.network", json={}, status=400
    )
    assert not get_effective_gas_price(web3, Network.Polygon)


def test_get_effective_gas_price__arb():
    gas_price = 125
    web3 = MagicMock(
        eth=MagicMock(
            gas_price=gas_price,
        ),
    )
    gas = get_effective_gas_price(web3, Network.Arbitrum)
    assert gas == gas_price * 1.1


def test_get_effective_gas_price__fantom():
    gas_price = 500
    web3 = MagicMock(
        eth=MagicMock(
            gas_price=gas_price,
        ),
    )
    gas = get_effective_gas_price(web3, Network.Fantom)
    assert gas == gas_price * GAS_BUFFER
