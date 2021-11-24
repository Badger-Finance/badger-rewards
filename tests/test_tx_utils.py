import pytest

from helpers.enums import Network
from tests.utils import set_env_vars

set_env_vars()

from config.singletons import env_config
from rewards.utils.tx_utils import get_transaction


@pytest.mark.parametrize(
    "network_info",
    [
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

)
def test_check_tx_receipt(mocker, network_info):
    discord = mocker.patch("rewards.utils.tx_utils.send_message_to_discord")
    web3 = env_config.get_web3(network_info["network"])
    assert get_transaction(
        web3, network_info["valid_tx"], 2, network_info["network"]
    )
    with pytest.raises(Exception):
        get_transaction(
            web3, network_info["invalid_tx"], 2, network_info["network"],
            tries=1
        )
    assert discord.called
