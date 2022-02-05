from collections import Counter
from decimal import Decimal

import pytest
import responses
from pytest import approx

from badger_api.requests import badger_api
from config.constants.addresses import BBADGER, BYWBTC
from config.constants.emissions import BOOST_CHAINS
from helpers.enums import BalanceType, Network
from rewards.snapshot.chain_snapshot import (
    chain_snapshot,
    chain_snapshot_usd,
    parse_sett_balances,
    sett_snapshot,
    total_twap_sett_snapshot,
)

BALANCES_DATA = {
    # Badger Token
    BBADGER: {
        '0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.04533617521779346,
    },
    # yearn_wbtc
    BYWBTC: {
        '0x05E41229Efca125057f4D96007Dc477312dB8feB': 1.04533617521779346,
    }
}

BADGER_PRICE = 31.205460272851376
YEARN_WBTC_PRICE = 57784.88168712999


@pytest.fixture
def mock_fetch_ch_balances(mocker):
    return mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_chain_balances",
        return_value=BALANCES_DATA
    )


@pytest.fixture
def responses_mock_token_balance():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        for network in BOOST_CHAINS:
            rsps.add(
                responses.GET, f"{badger_api}/tokens?chain={network}",
                json={'name': 'bBadger'},
                status=200
            )
        rsps.add_passthru('https://')
        yield rsps


@pytest.fixture
def mock_fetch_sett_balances(mocker):
    return mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_sett_balances",
        return_value={
            '0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.04533617521779346,
        }
    )


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_chain_snapshot__happy(mock_fetch_ch_balances, chain, responses_mock_token_balance):
    snapshot = chain_snapshot(chain, 123123)
    native = snapshot[BBADGER]
    assert native.type == BalanceType.Native
    assert native.ratio == 1
    assert native.token == BBADGER
    assert list(native.balances.values())[0] == approx(Decimal(
        list(BALANCES_DATA[BBADGER].values())[0]
    ))

    non_native = snapshot[BYWBTC]
    assert non_native.ratio == 1
    assert non_native.token == BYWBTC
    assert list(non_native.balances.values())[0] == approx(Decimal(
        list(BALANCES_DATA[BYWBTC].values())[0]
    ))


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


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_parse_sett_balances(chain):
    snapshot = parse_sett_balances(
        BBADGER,
        balances={
            '0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.04533617521779346,
        },
        chain=chain,
    )
    assert snapshot.type == BalanceType.Native
    assert snapshot.ratio == 1
    assert snapshot.token == BBADGER
    assert list(snapshot.balances.values())[0] == approx(Decimal(
        list(BALANCES_DATA[BBADGER].values())[0]
    ))


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_parse_sett_balances__blacklisted(chain, mocker):
    mocker.patch(
        "rewards.snapshot.chain_snapshot.REWARDS_BLACKLIST",
        {"0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": "some blacklisted stuff"}
    )
    snapshot = parse_sett_balances(
        BBADGER,
        balances={
            '0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.04533617521779346,
        },
        chain=chain,
    )
    assert snapshot.balances == {}


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_sett_snapshot(chain, mock_fetch_sett_balances, responses_mock_token_balance):
    snapshot = sett_snapshot(chain, 13710328, BBADGER)
    assert snapshot.type == BalanceType.Native
    assert snapshot.ratio == 1
    assert snapshot.token == BBADGER
    assert list(snapshot.balances.values())[0] == approx(Decimal(
        list(BALANCES_DATA[BBADGER].values())[0]
    ))


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
@pytest.mark.parametrize(
    "num_historical_snapshots",
    [3, 6, 5]
)
def test_total_harvest_sett_snapshot__even_balance(
        chain, num_historical_snapshots: int, mock_fetch_sett_balances, responses_mock_token_balance):
    snapshot = total_twap_sett_snapshot(
        chain, 13710328, 13710338, BBADGER,
        num_historical_snapshots=num_historical_snapshots
    )
    assert snapshot.type == BalanceType.Native
    assert snapshot.ratio == 1
    assert snapshot.token == BBADGER
    expected_amount: Decimal = Decimal(
        list(BALANCES_DATA[BBADGER].values())[0]
    ) * (num_historical_snapshots + 1)
    assert list(snapshot.balances.values())[0] == approx(expected_amount)


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_total_harvest_sett_snapshot__even_balance_single_snap(
        chain, mock_fetch_sett_balances, responses_mock_token_balance):
    """
    If num_historical_snapshots is 1, we should only take 2 snapshots for first and last blocks
    """
    snapshot = total_twap_sett_snapshot(
        chain, 13710328, 13710338, BBADGER,
        num_historical_snapshots=1
    )
    expected_amount: Decimal = Decimal(list(BALANCES_DATA[BBADGER].values())[0]) * 2
    assert list(snapshot.balances.values())[0] == approx(expected_amount)


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_total_harvest_sett_snapshot__even_balance_no_snapshots(
        chain, mock_fetch_sett_balances, responses_mock_token_balance):
    """
    If num_historical_snapshots is 0, we should only take end block snapshot
    """
    snapshot = total_twap_sett_snapshot(
        chain, 13710328, 13710338, BBADGER,
        num_historical_snapshots=0
    )
    expected_amount: Decimal = Decimal(list(BALANCES_DATA[BBADGER].values())[0])
    assert list(snapshot.balances.values())[0] == approx(expected_amount)


@pytest.mark.parametrize(
    "num_historical_snapshots",
    [14, 20, 100]
)
def test_total_harvest_sett_snapshot__invalid_rate(
        num_historical_snapshots: int, mock_fetch_sett_balances, responses_mock_token_balance):
    snapshot = total_twap_sett_snapshot(
        Network.Ethereum, 13710328, 13710338, BBADGER,
        num_historical_snapshots=num_historical_snapshots
    )
    assert snapshot.type == BalanceType.Native
    assert snapshot.ratio == 1
    assert snapshot.token == BBADGER
    # In this case only first and last snaps should be taken into account
    expected_amount: Decimal = Decimal(
        list(BALANCES_DATA[BBADGER].values())[0]
    ) * 2
    assert list(snapshot.balances.values())[0] == approx(expected_amount)


def test_total_harvest_sett_snapshot__uneven_balance(chain, mocker, responses_mock_token_balance):
    initial_balance = 0.045336
    with mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_sett_balances",
        side_effect=[
            {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': initial_balance},
            {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0.01},
            {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0},
            {'0x0000000000007F150Bd6f54c40A34d7C3d5e9f56': 0},
        ]
    ):
        snapshot = total_twap_sett_snapshot(
            Network.Ethereum, 13710328, 13710338, BBADGER,
            num_historical_snapshots=2
        )
    assert snapshot.token == BBADGER
    expected_amount: Decimal = Decimal((initial_balance + 0.01 + 0))
    assert expected_amount > initial_balance
    assert list(snapshot.balances.values())[0] == approx(expected_amount)


def test_total_harvest_sett_snapshot__invalid_blocks():
    with pytest.raises(AssertionError):
        total_twap_sett_snapshot(
            Network.Ethereum, 13710338, 13710328, BBADGER,
            num_historical_snapshots=1
        )


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_sett_snapshot__empty(mocker, chain):
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_sett_balances",
        return_value={}
    )
    snapshot = sett_snapshot(chain, 13710328, BBADGER)
    assert snapshot.balances == {}


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_sett_snapshot__raises(mocker, chain):
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_sett_balances",
        side_effect=Exception,
    )
    with pytest.raises(Exception):
        sett_snapshot(chain, 13710328, BBADGER)


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_chain_snapshot_usd__happy(
        chain, mock_fetch_ch_balances, mocker, responses_mock_token_balance
):
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_unboosted_vaults",
        return_value=[]
    )
    for boost_chain in BOOST_CHAINS:
        responses_mock_token_balance.add(
            responses.GET, f"{badger_api}/prices?chain={boost_chain}",
            json={
                BBADGER: BADGER_PRICE,
                BYWBTC: YEARN_WBTC_PRICE,
            },
            status=200
        )
    native, non_native = chain_snapshot_usd(chain, 13710328)
    # Make sure USD balance is calculated properly
    expected_balance_in_usd_native = Decimal(
        BADGER_PRICE *
        BALANCES_DATA[BBADGER]['0x0000000000007F150Bd6f54c40A34d7C3d5e9f56']
    )
    expected_balance_in_usd_non_native = Decimal(
        YEARN_WBTC_PRICE *
        BALANCES_DATA[BYWBTC]['0x05E41229Efca125057f4D96007Dc477312dB8feB']
    )
    assert native['0x0000000000007F150Bd6f54c40A34d7C3d5e9f56'] == approx(
        expected_balance_in_usd_native
    )
    assert non_native['0x05E41229Efca125057f4D96007Dc477312dB8feB'] == approx(
        expected_balance_in_usd_non_native
    )


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_chain_snapshot_usd__no_boost(chain, mock_fetch_ch_balances, mocker):
    # Make sure setts are excluded in case 'no_boost' variable contains them
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_unboosted_vaults",
        return_value=[BBADGER, BYWBTC]
    )
    assert chain_snapshot_usd(chain, 13710328) == (Counter(), Counter())


@pytest.mark.parametrize(
    "chain",
    [Network.Ethereum, Network.Arbitrum]
)
def test_chain_snapshot_usd__empty(chain, mock_fetch_ch_balances, mocker):
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_chain_balances",
        return_value={}
    )
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_unboosted_vaults",
        return_value=[]
    )
    assert chain_snapshot_usd(chain, 13710328) == (Counter(), Counter())


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
        chain_snapshot_usd(chain, 13710328)
