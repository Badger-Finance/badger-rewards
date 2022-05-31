from badger_api.config import get_api_base_path
from config.constants.addresses import BUNI_DIGG_WBTC, DIGG, WBTC
from config.constants.emissions import BOOST_CHAINS
from helpers.enums import Network
from rewards.classes.Snapshot import Snapshot
import responses
from rewards.feature_flags.feature_flags import DIGG_BOOST, flags
badger_api = get_api_base_path()


@responses.activate
def test_convert_to_usd_no_digg_boost():
    chain = Network.Ethereum
    flags.FLAGS[DIGG_BOOST] = False
    for chain in BOOST_CHAINS:
        responses.add(
            responses.GET,
            f"{badger_api}/prices?chain={chain}",
            json={
                DIGG: 100,
                WBTC: 50,
            },
            status=200,
        )
    ADDRESS = "0x00192Fb10dF37c9FB26829eb2CC623cd1BF599E8"
    snapshot = Snapshot(DIGG, {ADDRESS: 1}, ratio=1)
    usd_bals = snapshot.convert_to_usd(chain).balances
    assert usd_bals[ADDRESS] == 100


@responses.activate
def test_convert_to_usd_digg_boost():
    chain = Network.Ethereum
    flags.FLAGS[DIGG_BOOST] = True
    for chain in BOOST_CHAINS:
        responses.add(
            responses.GET,
            f"{badger_api}/prices?chain={chain}",
            json={
                WBTC: 50,
                DIGG: 10,
                BUNI_DIGG_WBTC: 500
            },
            status=200,
        )
    ADDRESS = "0x00192Fb10dF37c9FB26829eb2CC623cd1BF599E8"
    lp_snapshot = Snapshot(BUNI_DIGG_WBTC, {ADDRESS: 1})
    digg_snapshot = Snapshot(DIGG, {ADDRESS: 1})
    digg_usd = digg_snapshot.convert_to_usd(chain).balances
    assert digg_usd[ADDRESS] == 50
    lp_bals = lp_snapshot.convert_to_usd(chain).balances
    assert lp_bals[ADDRESS] == 1500
