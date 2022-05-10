from config.constants.addresses import DIGG, SLP_DIGG_WBTC, UNI_DIGG_WBTC
from helpers.enums import Abi, Network
from helpers.web3_utils import make_contract


class DiggUtils:
    def __init__(self):
        self.digg = make_contract(DIGG, abi_name=Abi.Digg, chain=Network.Ethereum)
        self.uni_digg_balance = self.digg.sharesOf(UNI_DIGG_WBTC).call()
        self.sushi_digg_balance = self.digg.sharesOf(SLP_DIGG_WBTC).call()
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


digg_utils = DiggUtils()
