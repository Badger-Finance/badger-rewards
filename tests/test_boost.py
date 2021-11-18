import json
import logging
import os

import pytest
from brownie import web3
from eth_account import Account

from config.singletons import env_config
from helpers.enums import Network
from rewards.aws.boost import add_user_data, download_boosts
from rewards.boost.calc_boost import badger_boost
from tests.cycle_utils import mock_upload_boosts
from tests.utils import (
    mock_boosts,
    mock_claimable_bals,
    mock_claimed_for,
    mock_tree,
    set_env_vars,
    test_address,
    test_key,
)

logger = logging.getLogger("test-boost")

set_env_vars()

from helpers.enums import Network
from rewards.aws.boost import upload_boosts


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


def mock_send_code_block_to_discord(
    msg: str, username: str, url: str = None
):
    logger.info(msg)


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
def mock_fns(monkeypatch):
    monkeypatch.setattr("rewards.aws.boost.s3.put_object", mock_put_object)


def test_upload_boost_staging(monkeypatch):
    mock_env_config_obj = mock_env_config()
    monkeypatch.setattr(
        "rewards.aws.boost.send_message_to_discord", mock_send_message_to_discord_stg
    )
    monkeypatch.setattr("rewards.aws.boost.env_config", mock_env_config_obj)

    upload_boosts(mock_boosts, Network.Ethereum)


def test_upload_boost_prod(monkeypatch):
    mock_env_config_obj = mock_env_config()
    mock_env_config_obj.test = False
    mock_env_config_obj.production = True
    monkeypatch.setattr(
        "rewards.aws.boost.send_message_to_discord", mock_send_message_to_discord_prod
    )
    monkeypatch.setattr("rewards.aws.boost.env_config", mock_env_config_obj)

    upload_boosts(mock_boosts, Network.Ethereum)

def test_boost_workflow(monkeypatch):
    monkeypatch.setattr(
        "rewards.aws.boost.send_message_to_discord", mock_send_message_to_discord_prod
    )
    monkeypatch.setattr("rewards.boost.calc_boost.send_code_block_to_discord", mock_send_code_block_to_discord)
    monkeypatch.setattr("rewards.aws.boost.download_boosts", lambda *args, **kwargs: mock_boosts)
    monkeypatch.setattr("rewards.aws.boost.upload_boosts", mock_upload_boosts)
    current_block = env_config.get_web3().eth.block_number
    user_data = badger_boost(current_block, Network.Ethereum)
    # mock upload boosts has asserts baked in to check nothing Decimal, and saves file to test serialization
    add_user_data(user_data, Network.Ethereum)