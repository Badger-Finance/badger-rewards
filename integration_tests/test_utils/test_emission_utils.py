import pytest
from config.constants.chain_mappings import SETTS
from helpers.enums import Network
from decimal import Decimal
from rewards.utils.emission_utils import get_across_lp_multiplier, get_nft_weight, get_token_weight


def test_get_nft_weight():
    chain = Network.Ethereum
    happy_cases = [
        ({"address": "0xe1e546e25A5eD890DFf8b8D005537c0d373497F8", "id": 1}, 200),
        ({"address": "0xe4605d46Fd0B3f8329d936a8b258D69276cBa264", "id": 97}, 10),
    ]
    bad_cases = [
        ({"address": "0xe1e546e25A5eD890DFf8b8D005537c0d373497F8", "id": 1}, 100),
        ({"address": "0xe1e546e25A5eD890DFf8b8D005537c0d373497F2", "id": 5}, 200),
    ]
    for happy_case in happy_cases:
        nft_data, weight = happy_case
        assert get_nft_weight(chain, nft_data["address"], nft_data["id"]) == Decimal(
            weight
        )
    with pytest.raises(Exception):
        for bad_case in bad_cases:
            bad_nft_data, weight = bad_case
            get_nft_weight(chain, bad_nft_data["address"], bad_nft_data["id"])


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


def test_get_across_lp_multiplier():
    assert get_across_lp_multiplier() > 1
