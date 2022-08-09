import pytest

from config.constants.addresses import ARB_BADGER
from config.constants.addresses import BADGER
from helpers.enums import Network
from rewards.snapshot.token_snapshot import token_snapshot
from tests.utils import TEST_WALLET, TEST_WALLET_ANOTHER


@pytest.fixture
def mock_fns(mocker):
    mocker.patch(
        "rewards.snapshot.token_snapshot.fetch_across_balances",
        return_value={
            TEST_WALLET: 10,
            TEST_WALLET_ANOTHER: 20
        }
    )
    mocker.patch(
        "rewards.snapshot.token_snapshot.fetch_token_balances",
        return_value=(
            {TEST_WALLET: 10, TEST_WALLET_ANOTHER: 50},
            {TEST_WALLET: 20, TEST_WALLET_ANOTHER: 30}
        )
    )
    mocker.patch(
        "rewards.snapshot.token_snapshot.fetch_fuse_pool_token",
        side_effect=[
            {TEST_WALLET: 10},
            {TEST_WALLET: 5}
        ]
    )


@pytest.mark.parametrize("chain", [Network.Ethereum, Network.Arbitrum])
def test_token_snapshot(chain, mock_fns):

    expected_badger_bals = {
        TEST_WALLET: 10 + 10 + 10,
        TEST_WALLET_ANOTHER: 20 + 50
    }
    expected_digg_bals = {
        TEST_WALLET: 20 + 5,
        TEST_WALLET_ANOTHER: 30
    }
    badger_snapshot, digg_snapshot = token_snapshot(chain, 100)
    assert badger_snapshot.balances == expected_badger_bals
    assert digg_snapshot.balances == expected_digg_bals

    if chain == Network.Ethereum:
        assert badger_snapshot.token == BADGER
    if chain == Network.Arbitrum:
        assert badger_snapshot.token == ARB_BADGER
