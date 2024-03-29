import responses

from decimal import Decimal

from badger_api.config import get_api_base_path
from config.constants.addresses import (
    BAURA_DIGG_WBTC,
    BUNI_DIGG_WBTC,
    BDIGG,
    DIGG,
    WBTC,
)
from helpers.enums import Network
from rewards.classes.Snapshot import Snapshot
from rewards.feature_flags.feature_flags import DIGG_BOOST, flags


badger_api = get_api_base_path()


@responses.activate
def test_convert_to_usd_no_digg_boost():
    chain = Network.Ethereum
    flags.FLAGS[DIGG_BOOST] = False
    responses.add(
        responses.GET,
        f"{badger_api}/prices?chain={chain}",
        json={
            DIGG: 100,
            WBTC: 50,
        },
        status=200,
    )
    address = "0x00192Fb10dF37c9FB26829eb2CC623cd1BF599E8"
    snapshot = Snapshot(DIGG, {address: 1}, ratio=1)
    usd_bals = snapshot.convert_to_usd(chain).balances
    assert usd_bals[address] == 100


@responses.activate
def test_convert_to_usd_digg_boost(mocker):
    chain = Network.Ethereum
    flags.FLAGS[DIGG_BOOST] = True

    mocker.patch(
        "rewards.classes.Snapshot.fetch_ppfs",
        return_value=(Decimal(str(1)), Decimal(str(1.1))),
    )
    responses.add(
        responses.GET,
        f"{badger_api}/prices?chain={chain}",
        json={
            WBTC: 50,
            DIGG: 10,
            BDIGG: 10,
            BUNI_DIGG_WBTC: 500,
            BAURA_DIGG_WBTC: 500,
        },
        status=200,
    )

    address = "0x00192Fb10dF37c9FB26829eb2CC623cd1BF599E8"
    lp_snapshot = Snapshot(BUNI_DIGG_WBTC, {address: 1}, ratio=0.5)
    aura_lp_snapshot = Snapshot(BAURA_DIGG_WBTC, {address: 1}, ratio=0.4)
    digg_snapshot = Snapshot(DIGG, {address: 1})
    bdigg_snapshot = Snapshot(BDIGG, {address: 1})

    digg_usd = digg_snapshot.convert_to_usd(chain).balances
    bdigg_usd = bdigg_snapshot.convert_to_usd(chain).balances
    lp_bals = lp_snapshot.convert_to_usd(chain).balances
    aura_lp_usd = aura_lp_snapshot.convert_to_usd(chain).balances

    assert digg_usd[address] == 50
    assert lp_bals[address] == 1250
    assert aura_lp_usd[address] == 1000
    assert bdigg_usd[address] == 55
