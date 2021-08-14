from config.env_config import env_config
from helpers.constants import DIGG
import json


class DiggUtils:
    def __init__(self):
        with open("abis/eth/Digg.json") as f:
            _digg_abi = json.load(f)
        self.digg = env_config.web3.eth.contract(
            address=env_config.web3.toChecksumAddress(DIGG), abi=_digg_abi
        )
        self.sharesPerFragment = self.digg.functions._sharesPerFragment().call()
        self.initialShares = self.digg.functions._initialSharesPerFragment().call()

    def sharesToFragments(self, shares):
        if shares == 0:
            return 0
        return self.sharesPerFragment / shares


diggUtils = DiggUtils()
