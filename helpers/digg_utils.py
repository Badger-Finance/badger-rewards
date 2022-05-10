from config.constants.addresses import DIGG, SLP_DIGG_WBTC, UNI_DIGG_WBTC
from helpers.enums import Abi, Network
from helpers.web3_utils import make_contract, make_token


class DiggUtils:
    def __init__(self):
        self.digg = make_contract(DIGG, abi_name=Abi.Digg, chain=Network.Ethereum)
        uni_digg = make_token(UNI_DIGG_WBTC, Network.Ethereum)
        sushi_digg = make_token(SLP_DIGG_WBTC, Network.Ethereum)
        self.uni_digg_ratio = self.get_shares(UNI_DIGG_WBTC) / uni_digg.totalSupply().call()
        self.sushi_digg_ratio = self.get_shares(SLP_DIGG_WBTC) / sushi_digg.totalSupply().call()
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

    def get_shares(self, address) -> int:
        return self.digg.sharesOf(address).call()


digg_utils = DiggUtils()
