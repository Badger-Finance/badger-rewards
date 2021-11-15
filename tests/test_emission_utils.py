import pytest

from helpers.constants import BIBBTC_CURVE_LP, BSBTC, BVECVX
from helpers.enums import Network
from rewards.utils.emission_utils import get_flat_emission_rate
from tests.utils import set_env_vars

set_env_vars()


def test_get_flat_emission_rate():
    chain = Network.Ethereum
    happy_cases = [(BVECVX, 1), (BSBTC, 0), (BIBBTC_CURVE_LP, 0.49)]

    for sett, rate in happy_cases:
        assert get_flat_emission_rate(sett, chain) == rate
    with pytest.raises(Exception):
        get_flat_emission_rate(BSBTC.lower(), chain)
