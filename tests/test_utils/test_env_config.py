import logging
import os

import pytest

from unittest.mock import MagicMock

os.environ["KUBE"] = "False"
os.environ["AWS_ACCESS_KEY_ID"] = ""
os.environ["AWS_SECRET_ACCESS_KEY"] = ""

from config.env_config import EnvConfig, NoHealthyNode
from helpers.enums import Environment, Network

logger = logging.getLogger("test-env-config")


def test_valid_environment():
    if "ENV" in os.environ:
        os.environ.pop("ENV")
    with pytest.raises(AssertionError):
        EnvConfig()

    os.environ["ENV"] = "test"
    env_config = EnvConfig()
    assert env_config.is_valid_config()


def test_get_environment():
    enum = [Environment.Test, Environment.Staging, Environment.Production]
    vals = ["test", "stg", "prod"]
    for expected, val in zip(enum, vals):
        if "ENV" in os.environ:
            os.environ.pop("ENV")
        os.environ["ENV"] = val
        env_config = EnvConfig()
        assert env_config.get_environment() == expected


def test_get_web3_happy(mocker):
    env_config = EnvConfig()
    env_config.web3[Network.Polygon] = [
        MagicMock(
            eth=MagicMock(
                get_block_number=MagicMock(
                    side_effect=Exception
                )
            ),
            provider=MagicMock(
                endpoint_uri="unhealthy-rpc.com"
            )
        ),
        MagicMock(
            eth=MagicMock(
                get_block_number=MagicMock(
                    return_value=1
                )
            ),
            provider=MagicMock(
                endpoint_uri="healthy-rpc.com"
            )
        ),
    ]
    web3 = env_config.get_web3(Network.Polygon)
    assert web3.provider.endpoint_uri == "healthy-rpc.com"


def test_get_web3_unhappy(mocker):
    env_config = EnvConfig()
    env_config.web3[Network.Polygon] = [
        MagicMock(
            eth=MagicMock(
                get_block_number=MagicMock(
                    side_effect=Exception
                )
            ),
            provider=MagicMock(
                endpoint_uri="unhealthy-rpc.com"
            )
        ),
        MagicMock(
            eth=MagicMock(
                get_block_number=MagicMock(
                    side_effect=Exception
                )
            ),
            provider=MagicMock(
                endpoint_uri="unhealthy-rpc-2.com"
            )
        ),
    ]
    with pytest.raises(NoHealthyNode):
        env_config.get_web3(Network.Polygon)
