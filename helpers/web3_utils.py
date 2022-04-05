import json
from web3 import Web3
from web3.contract import ContractFunctions

from config.constants.chain_mappings import EMISSIONS_CONTRACTS
from config.singletons import env_config
from helpers.enums import Abi


def load_abi(abi: Abi):
    with open(f"abis/eth/{abi}.json") as fp:
        abi = json.load(fp)
    return abi


def make_contract(address: str, abi_name: Abi, chain: str) -> ContractFunctions:
    w3 = env_config.get_web3(chain)
    return make_contract_w3(address, abi_name, w3)


def make_contract_w3(address: str, abi_name: Abi, w3: Web3):
    abi = load_abi(abi_name)
    return w3.eth.contract(address=w3.toChecksumAddress(address), abi=abi).functions


def get_badger_tree(chain: str) -> ContractFunctions:
    return make_contract(
        EMISSIONS_CONTRACTS[chain]["BadgerTree"], abi_name=Abi.BadgerTree, chain=chain
    )


def make_token(token_addr: str, chain: str) -> ContractFunctions:
    return make_contract(token_addr, abi_name=Abi.ERC20, chain=chain)
