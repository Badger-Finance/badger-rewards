import json
import os

from dotenv import load_dotenv

from config.singletons import env_config
from helpers.constants import BOOST_BLOCK_DELAY
from helpers.enums import Network
from rewards.boost.boost_utils import calc_boost_balances

load_dotenv()

chain = Network.Ethereum

current_block = env_config.get_web3(chain).eth.block_number

nft_native_setts, _ = calc_boost_balances(
        current_block - BOOST_BLOCK_DELAY, chain
    )
no_nft_native_setts, _ = calc_boost_balances(current_block - BOOST_BLOCK_DELAY, chain, False)

for addr in nft_native_setts.keys():
    nft_native_setts[addr] = float(nft_native_setts[addr])

for addr in no_nft_native_setts.keys():
    no_nft_native_setts[addr] = float(no_nft_native_setts[addr])

differences = {}

for addr in nft_native_setts.keys():
    if addr not in no_nft_native_setts:
        differences[addr] = {
            'nft': nft_native_setts[addr],
            'no_nft': 0,
            'diff': nft_native_setts[addr] - 0
        }
    elif no_nft_native_setts[addr] + 150 <= nft_native_setts[addr]:
        differences[addr] = {
            'nft': nft_native_setts[addr],
            'no_nft': no_nft_native_setts[addr],
            'diff': nft_native_setts[addr] - no_nft_native_setts[addr]
        }

with open('boost-differences.json', "w") as fp:
    json.dump(differences, fp, indent=4)

