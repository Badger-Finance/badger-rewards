import json

from web3.contract import ContractFunctions

from config.singletons import env_config
from helpers.constants import EMISSIONS_CONTRACTS


def make_contract(address: str, abi_name: str, chain: str) -> ContractFunctions:
    with open(f"abis/eth/{abi_name}.json") as fp:
        abi = json.load(fp)

    w3 = env_config.get_web3(chain)
    return w3.eth.contract(address=w3.toChecksumAddress(address), abi=abi).functions


def get_badger_tree(chain: str) -> ContractFunctions:
    return make_contract(
        EMISSIONS_CONTRACTS[chain]["BadgerTree"], abi_name="BadgerTreeV2", chain=chain
    )


def make_token(token_addr: str, chain: str):
    return make_contract(token_addr, abi_name="ERC20", chain=chain)
