from config.env_config import env_config
from helpers.constants import DIGG
from helpers.web3_utils import make_contract
import json
from helpers.enums import Network


class DiggUtils:
    def __init__(self):
        self.digg = make_contract(DIGG, abi_name="Digg", chain=Network.Ethereum)
        self.shares_per_fragment = self.digg._sharesPerFragment().call()
        self.initial_shares = self.digg._initialSharesPerFragment().call()

    def shares_to_fragments(self, shares: int) -> float:
        if shares == 0:
            return 0
        return self.shares_per_fragment / shares


digg_utils = DiggUtils()
