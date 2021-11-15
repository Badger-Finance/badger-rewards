import pytest

from helpers.constants import (BBADGER, BIBBTC_CURVE_LP, BSBTC, BVECVX,
                               UNI_BADGER_WBTC)
from helpers.enums import Network
from rewards.utils.emission_utils import (get_flat_emission_rate,
                                          get_token_weight)
from tests.utils import set_env_vars

set_env_vars()


def test_get_flat_emission_rate():
    chain = Network.Ethereum
    happy_cases = [(BVECVX, 1), (BSBTC, 0), (BIBBTC_CURVE_LP, 0.49)]

    for sett, rate in happy_cases:
        assert get_flat_emission_rate(sett, chain) == rate
    with pytest.raises(Exception):
        get_flat_emission_rate(BSBTC.lower(), chain)


def test_get_token_weight():
    all_cases = {Network.Ethereum: {BBADGER: 1, UNI_BADGER_WBTC: 0.5, BSBTC: 1}}
    for network, cases in all_cases.items():
        print(network)
        for token, weight in cases.items():
            assert get_token_weight(token, network) == weight
