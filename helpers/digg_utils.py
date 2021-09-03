from config.env_config import env_config
from helpers.constants import DIGG
from helpers.web3_utils import make_contract
import json


class DiggUtils:
    def __init__(self):
        self.digg = make_contract(DIGG, abiName="Digg", chain="eth")
        self.sharesPerFragment = self.digg._sharesPerFragment().call()
        self.initialShares = self.digg._initialSharesPerFragment().call()

    def sharesToFragments(self, shares: int) -> float:
        if shares == 0:
            return 0
        return self.sharesPerFragment / shares


digg_utils = DiggUtils()
