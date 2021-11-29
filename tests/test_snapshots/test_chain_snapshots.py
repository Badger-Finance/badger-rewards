from decimal import Decimal

import pytest

from helpers.enums import BalanceType, Network
from rewards.snapshot.chain_snapshot import chain_snapshot

BADGER_TOKEN_ADDR = "0x19D97D8fA813EE2f51aD4B4e04EA08bAf4DFfC28"
YEARN_WBTC_ADDR = "0x4b92d19c11435614CD49Af1b589001b7c08cD4D5"

BALANCES_DATA = {
    # Badger Token
    BADGER_TOKEN_ADDR: {
        '0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.04533617521779346,
    },
    # yearn_wbtc
    YEARN_WBTC_ADDR: {
        '0x05E41229Efca125057f4D96007Dc477312dB8feB': 1.04533617521779346,
    }
}


@pytest.fixture
def mock_fetch_ch_balances(mocker):
    return mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_chain_balances",
        return_value=BALANCES_DATA
    )


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_chain_snapshot__happy(mock_fetch_ch_balances, chain):
    snapshot = chain_snapshot(chain, 123123)
    native = snapshot[BADGER_TOKEN_ADDR]
    assert native.type == BalanceType.Native
    assert native.ratio == 1
    assert native.token == BADGER_TOKEN_ADDR
    assert list(native.balances.values())[0] == round(Decimal(
        list(BALANCES_DATA[BADGER_TOKEN_ADDR].values())[0]
    ), 17)

    non_native = snapshot[YEARN_WBTC_ADDR]
    assert non_native.ratio == 1
    assert non_native.token == YEARN_WBTC_ADDR
    assert list(non_native.balances.values())[0] == round(Decimal(
        list(BALANCES_DATA[YEARN_WBTC_ADDR].values())[0]
    ), 16)


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_chain_snapshot__empty(mocker, chain):
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_chain_balances",
        return_value={}
    )
    snapshot = chain_snapshot(chain, 123123)
    assert snapshot == {}


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_chain_snapshot__raises(mocker, chain):
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_chain_balances",
        side_effect=Exception,
    )
    with pytest.raises(Exception):
        chain_snapshot(chain, 123123)
