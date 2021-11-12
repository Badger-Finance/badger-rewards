from functools import lru_cache
from helpers.constants import EMISSIONS_CONTRACTS
from helpers.web3_utils import make_contract

@lru_cache
def get_emission_control(chain):
    return make_contract(EMISSIONS_CONTRACTS[chain]["EmissionControl"], "EmissionControl", chain)


def get_token_weight(token, chain):
    token_weight = get_emission_control(chain).tokenWeight(token).call()
    return 1 if token_weight == 0 else token_weight


def get_flat_emission_rate(token, chain):
    return get_emission_control(chain).proRataEmissionRate(token).call() / 1e4
