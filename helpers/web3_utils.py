from helpers.constants import EMISSIONS_CONTRACTS
from config.env_config import env_config
import json


def make_contract(address: str, abiName: str, chain: str):
    with open("abis/eth/{}.json".format(abiName)) as fp:
        abi = json.load(fp)

    w3 = env_config.get_web3(chain)
    return w3.eth.contract(address=w3.toChecksumAddress(address), abi=abi)


def get_badger_tree(chain: str):
    return make_contract(EMISSIONS_CONTRACTS[chain]["BadgerTree"], abiName="BadgerTreeV2", chain=chain)
