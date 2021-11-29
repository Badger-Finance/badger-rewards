import pytest

from helpers.constants import SETTS
from helpers.enums import Network
from tests.utils import set_env_vars

set_env_vars()

from rewards.utils.emission_utils import (
    fetch_setts,
    fetch_unboosted_vaults,
    get_flat_emission_rate,
    get_nft_weight,
    get_token_weight,
)


class MockTime:
    def __init__(self):
        pass

    def time(self):
        return 1637086012


def mock_fetch_setts(*args, **kwargs):
    return [
        SETTS[Network.Ethereum]["ren_crv"],
        SETTS[Network.Ethereum]["sbtc_crv"],
        SETTS[Network.Ethereum]["cvx"],
    ]


def test_get_flat_emission_rate():
    chain = Network.Ethereum
    happy_cases = [
        (SETTS[Network.Ethereum]["bvecvx"], 1),
        (SETTS[Network.Ethereum]["sbtc_crv"], 0),
        (SETTS[Network.Ethereum]["ibbtc_crv"], 0.49),
    ]

    for sett, rate in happy_cases:
        assert get_flat_emission_rate(sett, chain) == rate
    with pytest.raises(Exception):
        get_flat_emission_rate(SETTS[Network.Ethereum]["sbtc_crv"].lower(), chain)


def test_get_nft_weight():
    chain = Network.Ethereum
    happy_cases = [
        ({"address":"0xe1e546e25A5eD890DFf8b8D005537c0d373497F8", "id": 1}, 200),
        ({"address":"0xe4605d46Fd0B3f8329d936a8b258D69276cBa264", "id": 97})
    ]
    bad_cases = [
         ({"address":"0xe1e546e25A5eD890DFf8b8D005537c0d373497F8", "id": 1}, 100),
         ({"address":"0xe1e546e25A5eD890DFf8b8D005537c0d373497F2", "id": 5}, 200),
    ]
    for nft_data, weight in happy_cases:
        assert get_nft_weight(chain, nft_data["address"], nft_data["id"]) == weight
    with pytest.raises(Exception):
        for nft_data, weight in bad_cases:
            get_nft_weight(chain, nft_data["address"], nft_data["id"]) == weight

            
    


def test_get_token_weight():
    all_cases = {
        Network.Ethereum: {
            SETTS[Network.Ethereum]["badger"]: 1,
            SETTS[Network.Ethereum]["uni_badger_wbtc"]: 0.5,
            SETTS[Network.Ethereum]["sbtc_crv"]: 1,
        }
    }
    for network, cases in all_cases.items():
        for token, weight in cases.items():
            assert get_token_weight(token, network) == weight


def test_fetch_unboosted_vaults(monkeypatch):
    monkeypatch.setattr("rewards.utils.emission_utils.fetch_setts", mock_fetch_setts)
    mock_time = MockTime()
    monkeypatch.setattr("rewards.utils.emission_utils.time", mock_time)
    unboosted_vaults = [SETTS[Network.Ethereum]["cvx"]]
    vaults = fetch_unboosted_vaults(Network.Ethereum)
    assert vaults == unboosted_vaults
