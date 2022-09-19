import os

import pytest
from brownie import accounts
from brownie import web3
from eth_account import Account
from moto.core import patch_resource

from rewards.aws.helpers import dynamodb
from tests.utils import mock_get_claimable_data
from tests.utils import set_env_vars
from tests.utils import test_address
from tests.utils import test_key

set_env_vars()
os.environ["private"] = test_key

from config.singletons import env_config
from helpers.enums import Network
from rewards.aws.helpers import get_secret
from tests.test_utils.cycle_utils import (
    mock_badger_tree,
    mock_cycle,
    mock_download_boosts,
    mock_tree_manager,
    mock_upload_boosts,
    mock_upload_tree,
)


@pytest.fixture(autouse=True)
def mock_fns(mocker):
    mocker.patch("rewards.calc_rewards.download_boosts", mock_download_boosts)
    mocker.patch(
        "rewards.calc_rewards.download_proposed_boosts", mock_download_boosts
    )
    mocker.patch("rewards.calc_rewards.upload_boosts", mock_upload_boosts)
    mocker.patch(
        "rewards.calc_rewards.upload_proposed_boosts", mock_upload_boosts
    )
    mocker.patch("rewards.calc_rewards.upload_tree", mock_upload_tree)
    mocker.patch(
        "rewards.snapshot.claims_snapshot.get_claimable_data", mock_get_claimable_data
    )


@pytest.fixture(autouse=True)
def set_env_config():
    env_config.test = False
    env_config.staging = False
    env_config.production = True
    env_config.get_web3 = lambda chain: web3


@pytest.fixture
def chain():
    return Network.Ethereum


@pytest.fixture
def keeper_address():
    return test_address


@pytest.fixture
def cycle_account():
    cycle_key = get_secret(
        "arn:aws:secretsmanager:us-west-1:747584148381:secret:/botsquad/cycle_0/private",
        "private",
        assume_role_arn="arn:aws:iam::747584148381:role/cycle20210908001427790200000001",
        kube=env_config.kube,
    )
    return Account.from_key(cycle_key)


@pytest.fixture(autouse=True)
def badger_tree(chain, keeper_address):
    badger_tree = mock_badger_tree(chain, keeper_address, accounts[0])
    return badger_tree


@pytest.fixture
def tree_manager(chain, cycle_account, badger_tree):
    tree_manager = mock_tree_manager(chain, cycle_account)
    return tree_manager


def test_cycle(tree_manager, badger_tree, keeper_address, mocker, setup_dynamodb):
    patch_resource(dynamodb)
    accounts[0].transfer(keeper_address, "10 ether", priority_fee="2 gwei")
    mock_cycle(tree_manager, badger_tree, keeper_address)
