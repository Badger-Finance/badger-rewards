from collections import Counter
from decimal import Decimal

import pytest
import responses
from pytest import approx

from badger_api.requests import badger_api
from helpers.constants import BBADGER_ADDRESS, BOOST_CHAINS, YEARN_WBTC_ADDRESS
from helpers.enums import BalanceType, Network
from rewards.snapshot.chain_snapshot import (
    chain_snapshot,
    chain_snapshot_usd,
    parse_sett_balances,
    sett_snapshot,
)

BALANCES_DATA = {
    # Badger Token
    BBADGER_ADDRESS: {
        "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 0.04533617521779346,
    },
    # yearn_wbtc
    YEARN_WBTC_ADDRESS: {
        "0x05E41229Efca125057f4D96007Dc477312dB8feB": 1.04533617521779346,
    },
}

BADGER_PRICE = 31.205460272851376
YEARN_WBTC_PRICE = 57784.88168712999


@pytest.fixture
def mock_fetch_ch_balances(mocker):
    return mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_chain_balances",
        return_value=BALANCES_DATA,
    )


@pytest.fixture
def mock_fetch_sett_balances(mocker):
    return mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_sett_balances",
        return_value={
            "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 0.04533617521779346,
        },
    )


@pytest.mark.parametrize("chain", [Network.Ethereum, Network.Arbitrum])
@responses.activate
def test_chain_snapshot__happy(mock_fetch_ch_balances, chain):
    responses.add(
        responses.GET,
        f"{badger_api}/tokens?chain={chain}",
        json={"name": "bBadger"},
        status=200,
    )
    responses.add_passthru("https://")
    snapshot = chain_snapshot(chain, 123123)
    native = snapshot[BBADGER_ADDRESS]
    assert native.type == BalanceType.Native
    assert native.ratio == 1
    assert native.token == BBADGER_ADDRESS
    assert list(native.balances.values())[0] == approx(
        Decimal(list(BALANCES_DATA[BBADGER_ADDRESS].values())[0])
    )

    non_native = snapshot[YEARN_WBTC_ADDRESS]
    assert non_native.ratio == 1
    assert non_native.token == YEARN_WBTC_ADDRESS
    assert list(non_native.balances.values())[0] == approx(
        Decimal(list(BALANCES_DATA[YEARN_WBTC_ADDRESS].values())[0])
    )


@pytest.mark.parametrize("chain", [Network.Ethereum, Network.Arbitrum])
def test_chain_snapshot__empty(mocker, chain):
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_chain_balances", return_value={}
    )
    snapshot = chain_snapshot(chain, 123123)
    assert snapshot == {}


@pytest.mark.parametrize("chain", [Network.Ethereum, Network.Arbitrum])
def test_chain_snapshot__raises(mocker, chain):
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_chain_balances",
        side_effect=Exception,
    )
    with pytest.raises(Exception):
        chain_snapshot(chain, 123123)


@pytest.mark.parametrize("chain", [Network.Ethereum, Network.Arbitrum])
def test_parse_sett_balances(chain):
    snapshot = parse_sett_balances(
        BBADGER_ADDRESS,
        balances={
            "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 0.04533617521779346,
        },
        chain=chain,
    )
    assert snapshot.type == BalanceType.Native
    assert snapshot.ratio == 1
    assert snapshot.token == BBADGER_ADDRESS
    assert list(snapshot.balances.values())[0] == approx(
        Decimal(list(BALANCES_DATA[BBADGER_ADDRESS].values())[0])
    )


@pytest.mark.parametrize("chain", [Network.Ethereum, Network.Arbitrum])
@responses.activate
def test_sett_snapshot(chain, mock_fetch_sett_balances):
    responses.add(
        responses.GET,
        f"{badger_api}/tokens?chain={chain}",
        json={"name": "bBadger"},
        status=200,
    )
    responses.add_passthru("https://")
    snapshot = sett_snapshot(chain, 13710328, BBADGER_ADDRESS)
    assert snapshot.type == BalanceType.Native
    assert snapshot.ratio == 1
    assert snapshot.token == BBADGER_ADDRESS
    assert list(snapshot.balances.values())[0] == approx(
        Decimal(list(BALANCES_DATA[BBADGER_ADDRESS].values())[0])
    )


@pytest.mark.parametrize("chain", [Network.Ethereum, Network.Arbitrum])
def test_sett_snapshot__empty(mocker, chain):
    mocker.patch("rewards.snapshot.chain_snapshot.fetch_sett_balances", return_value={})
    snapshot = sett_snapshot(chain, 13710328, BBADGER_ADDRESS)
    assert snapshot.balances == {}


@pytest.mark.parametrize("chain", [Network.Ethereum, Network.Arbitrum])
def test_sett_snapshot__raises(mocker, chain):
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_sett_balances",
        side_effect=Exception,
    )
    with pytest.raises(Exception):
        sett_snapshot(chain, 13710328, BBADGER_ADDRESS)


@pytest.mark.parametrize("chain", [Network.Ethereum, Network.Arbitrum])
@responses.activate
def test_chain_snapshot_usd__happy(chain, mock_fetch_ch_balances, mocker):
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_unboosted_vaults", return_value=[]
    )
    responses.add(
        responses.GET,
        f"{badger_api}/tokens?chain={chain}",
        json={"name": "bBadger"},
        status=200,
    )
    for boost_chain in BOOST_CHAINS:
        responses.add(
            responses.GET,
            f"{badger_api}/prices?chain={boost_chain}",
            json={
                BBADGER_ADDRESS: BADGER_PRICE,
                YEARN_WBTC_ADDRESS: YEARN_WBTC_PRICE,
            },
            status=200,
        )
    responses.add_passthru("https://")
    native, non_native = chain_snapshot_usd(chain, 13710328)
    # Make sure USD balance is calculated properly
    expected_balance_in_usd_native = Decimal(
        BADGER_PRICE
        * BALANCES_DATA[BBADGER_ADDRESS]["0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"]
    )
    expected_balance_in_usd_non_native = Decimal(
        YEARN_WBTC_PRICE
        * BALANCES_DATA[YEARN_WBTC_ADDRESS][
            "0x05E41229Efca125057f4D96007Dc477312dB8feB"
        ]
    )
    assert native["0x0000000000007F150Bd6f54c40A34d7C3d5e9f56"] == approx(
        expected_balance_in_usd_native
    )
    assert non_native["0x05E41229Efca125057f4D96007Dc477312dB8feB"] == approx(
        expected_balance_in_usd_non_native
    )


@pytest.mark.parametrize("chain", [Network.Ethereum, Network.Arbitrum])
def test_chain_snapshot_usd__no_boost(chain, mock_fetch_ch_balances, mocker):
    # Make sure setts are excluded in case 'no_boost' variable contains them
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_unboosted_vaults",
        return_value=[BBADGER_ADDRESS, YEARN_WBTC_ADDRESS],
    )
    assert chain_snapshot_usd(chain, 13710328) == (Counter(), Counter())


@pytest.mark.parametrize("chain", [Network.Ethereum, Network.Arbitrum])
def test_chain_snapshot_usd__empty(chain, mock_fetch_ch_balances, mocker):
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_chain_balances", return_value={}
    )
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_unboosted_vaults", return_value=[]
    )
    assert chain_snapshot_usd(chain, 13710328) == (Counter(), Counter())


@pytest.mark.parametrize("chain", [Network.Ethereum, Network.Arbitrum])
def test_chain_snapshot__raises(mocker, chain):
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_chain_balances",
        side_effect=Exception,
    )
    with pytest.raises(Exception):
        chain_snapshot_usd(chain, 13710328)
