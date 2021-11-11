from helpers.constants import EMISSIONS_CONTRACTS
from helpers.enums import Network
from helpers.web3_utils import make_contract


class EmissionControl:
    def __init__(self, chain: Network) -> None:
        self.contract = make_contract(
            EMISSIONS_CONTRACTS[chain]["EmissionControl"]
        )
        
    def get_token_weight(self, token):
        token_weight = self.contract.tokenWeight.call(token) / 1e4
        return 1 if token_weight == 0 else token_weight
        
    def get_flat_emission_rate(self, sett):
        return self.contract.proRataEmissionRate.call(sett) / 1e4
