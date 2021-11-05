import pytest
import json
import os
import logging
from brownie import web3
from eth_account import Account
from tests.utils import (
    test_address,
    test_key,
    mock_tree,
    mock_claimable_bals,
    mock_claimed_for,
    set_env_vars,
)

logger = logging.getLogger("test-boost")

set_env_vars()

from rewards.aws.boost import upload_boosts
from helpers.enums import Network


def mock_send_message_to_discord_stg(
    title: str, description: str, fields: list, username: str, url: str = ""
):
    logger.info(description)
    assert "s3://badger-staging-merkle-proofs/" in description
    assert "s3://badger-merkle-proofs/" not in description


def mock_send_message_to_discord_prod(
    title: str, description: str, fields: list, username: str, url: str = ""
):
    logger.info(description)
    assert "s3://badger-staging-merkle-proofs/" not in description
    assert "s3://badger-merkle-proofs/" in description


def mock_env_config():
    class MockEth:
        def __init__(self):
            self.chain_id = 1

    class MockWeb3:
        def __init__(self):
            self.eth = MockEth()

    class MockEnvConfig:
        def __init__(self):
            self.test = True
            self.staging = False
            self.production = False

        def get_web3(self, chain: str):
            return MockWeb3()

    return MockEnvConfig()


def mock_put_object(*args, **kwargs):
    return True


@pytest.fixture(autouse=True)
def mock_fns(monkeypatch):
    monkeypatch.setattr("rewards.aws.boost.s3.put_object", mock_put_object)


def test_upload_boost_staging(monkeypatch):
    mock_env_config_obj = mock_env_config()
    monkeypatch.setattr(
        "rewards.aws.boost.send_message_to_discord", mock_send_message_to_discord_stg
    )
    monkeypatch.setattr("rewards.aws.boost.env_config", mock_env_config_obj)

    mock_boost_data = {"userData": [1, 2, 3, 4]}
    upload_boosts(mock_boost_data, Network.Ethereum)


def test_upload_boost_prod(monkeypatch):
    mock_env_config_obj = mock_env_config()
    mock_env_config_obj.test = False
    mock_env_config_obj.production = True
    monkeypatch.setattr(
        "rewards.aws.boost.send_message_to_discord", mock_send_message_to_discord_prod
    )
    monkeypatch.setattr("rewards.aws.boost.env_config", mock_env_config_obj)

    mock_boost_data = {"userData": [1, 2, 3, 4]}
    upload_boosts(mock_boost_data, Network.Ethereum)