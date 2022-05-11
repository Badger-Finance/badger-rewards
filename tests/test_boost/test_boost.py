import logging

import pytest
from brownie import web3

from tests.utils import (
    mock_boosts,
    mock_send_message_to_discord_prod,
    mock_send_message_to_discord_stg,
    set_env_vars,
)

logger = logging.getLogger("test-boost")

set_env_vars()

from helpers.enums import Network
from rewards.aws.boost import upload_boosts


def mock_env_config():
    class MockEnvConfig:
        def __init__(self):
            self.test = True
            self.staging = False
            self.production = False

        def get_web3(self, chain: str):
            return web3

    return MockEnvConfig()


def mock_put_object(*args, **kwargs):
    return True


@pytest.fixture(autouse=True)
def mock_fns(mocker):
    mocker.patch("rewards.aws.boost.s3.put_object", mock_put_object)


def test_upload_boost_staging(mocker):
    mock_env_config_obj = mock_env_config()
    mocker.patch(
        "rewards.aws.boost.send_message_to_discord", mock_send_message_to_discord_stg
    )
    mocker.patch("rewards.aws.boost.env_config", mock_env_config_obj)

    upload_boosts(mock_boosts, Network.Ethereum)


def test_upload_boost_prod(mocker):
    mock_env_config_obj = mock_env_config()
    mock_env_config_obj.test = False
    mock_env_config_obj.production = True
    mocker.patch(
        "rewards.aws.boost.send_message_to_discord", mock_send_message_to_discord_prod
    )
    mocker.patch("rewards.aws.boost.env_config", mock_env_config_obj)

    upload_boosts(mock_boosts, Network.Ethereum)
