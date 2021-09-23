from web3.contract import ContractFunctions
from helpers.constants import EMISSIONS_CONTRACTS
from config.env_config import env_config
import json


def make_contract(address: str, abi_name: str, chain: str) -> ContractFunctions:
    with open(f"abis/eth/{abi_name}.json") as fp:
        abi = json.load(fp)

    w3 = env_config.get_web3(chain)
    return w3.eth.contract(address=w3.toChecksumAddress(address), abi=abi).functions


def get_badger_tree(chain: str) -> ContractFunctions:
    return make_contract(
        EMISSIONS_CONTRACTS[chain]["BadgerTree"], abi_name="BadgerTreeV2", chain=chain
    )
