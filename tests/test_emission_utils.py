import pytest

from helpers.constants import SETTS
from helpers.enums import Network
from rewards.utils.emission_utils import get_flat_emission_rate, get_token_weight
from tests.utils import set_env_vars

set_env_vars()


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