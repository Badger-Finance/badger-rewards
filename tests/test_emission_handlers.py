from rewards.classes.Snapshot import Snapshot
from rewards.emission_handlers import (
    fuse_pool_handler,
    ibbtc_peak_handler,
    treasury_handler,
    unclaimed_rewards_handler
)
import config.constants.addresses as addresses
from tests.utils import (
    CLAIMABLE_BALANCES_DATA_ETH,
    TEST_WALLET,
    TEST_WALLET_ANOTHER,
    mock_get_claimable_data
)
from decimal import Decimal


def test_unclaimed_rewards_handler(monkeypatch, fetch_token_mock):
    monkeypatch.setattr(
        "rewards.snapshot.claims_snapshot.get_claimable_data", mock_get_claimable_data
    )
    token = addresses.BCVXCRV
    amount = 1e18
    rewards_list = unclaimed_rewards_handler(
        amount,
        token,
        sett=addresses.BCVXCRV,
        block=100
    )
    test_wallet_rewards = CLAIMABLE_BALANCES_DATA_ETH["rewards"][TEST_WALLET]
    test_wallet_2_rewards = CLAIMABLE_BALANCES_DATA_ETH["rewards"][TEST_WALLET_ANOTHER]

    test_bcvxcrv = next((x for x in test_wallet_rewards if x["address"] == addresses.BCVXCRV))
    test_2_bcvxcrv = next((x for x in test_wallet_2_rewards if x["address"] == addresses.BCVXCRV))

    test_bcvxcrv = int(test_bcvxcrv["balance"])
    test_2_bcvxcrv = int(test_2_bcvxcrv["balance"])
    test_wallet_recieved_rewards = (test_bcvxcrv / (test_bcvxcrv + test_2_bcvxcrv)) * 1e18
    test_wallet_2_recieved_rewards = (test_2_bcvxcrv / (test_bcvxcrv + test_2_bcvxcrv)) * 1e18

    assert rewards_list.claims[TEST_WALLET][token] == Decimal(
        test_wallet_recieved_rewards
    )
    assert rewards_list.claims[TEST_WALLET_ANOTHER][token] == Decimal(
        test_wallet_2_recieved_rewards
    )


def test_unclaimed_rewards_handler_no_claimable(monkeypatch, fetch_token_mock):
    monkeypatch.setattr(
        "rewards.snapshot.claims_snapshot.get_claimable_data", mock_get_claimable_data
    )
    rewards_list = unclaimed_rewards_handler(
        1e18,
        addresses.BCVXCRV,
        addresses.BOR,
        100
    )
    assert len(rewards_list.claims) == 0


def test_ibbtc_peak_handler():
    token = addresses.BCVXCRV
    rewards_list = ibbtc_peak_handler(
        1e18,
        token,
        addresses.BVECVX,
        100
    )
    assert rewards_list.claims[addresses.IBBTC_MULTISIG][token] == 1e18


def test_treasury_handler():
    token = addresses.BCVXCRV
    rewards_list = treasury_handler(
        1e18,
        token,
        addresses.BVECVX,
        100
    )
    assert rewards_list.claims[addresses.TREASURY_OPS][token] == 1e18


def test_fuse_pool_handler(mocker):
    sett = addresses.BVECVX
    token = addresses.BCVXCRV
    snapshot = Snapshot(
        sett,
        balances={
            TEST_WALLET: 5000,
            TEST_WALLET_ANOTHER: 5000
        }
    )

    mocker.patch(
        "rewards.emission_handlers.fuse_snapshot_of_token",
        return_value=snapshot
    )
    amount = 1e18
    rewards_list = fuse_pool_handler(
        amount,
        token,
        sett,
        100
    )
    test_percentage = snapshot.percentage_of_total(TEST_WALLET)
    test_ano_percentage = snapshot.percentage_of_total(TEST_WALLET_ANOTHER)
    assert rewards_list.claims[TEST_WALLET][token] == test_percentage * Decimal(amount)
    assert rewards_list.claims[TEST_WALLET_ANOTHER][token] == test_ano_percentage * Decimal(amount)
