from config.constants.addresses import DIGG
from helpers.enums import Abi, Network
from helpers.web3_utils import make_contract


class DiggUtils:
    def __init__(self):
        self.digg = make_contract(DIGG, abi_name=Abi.Digg, chain=Network.Ethereum)
        self.shares_per_fragment = self.digg._sharesPerFragment().call()
        self.initial_shares = self.digg._initialSharesPerFragment().call()

    def shares_to_fragments(self, shares: int) -> float:
        if shares == 0:
            return 0
        return shares / self.shares_per_fragment

    def fragments_to_shares(self, fragments: int) -> float:
        if fragments == 0:
            return 0
        return fragments * self.shares_per_fragment
