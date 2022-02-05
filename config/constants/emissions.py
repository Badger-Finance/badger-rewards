from dotmap import DotMap
from web3 import Web3

import config.constants.addresses as addresses
from helpers.enums import BalanceType, BotType, BucketType, Environment, Network

EMISSIONS_BLACKLIST = {
    addresses.DEV_MULTISIG: "Badger Dev Multisig",
    addresses.TECH_OPS: "Badger Tech Ops",
    addresses.TREASURY_OPS: "Badger Treasury Ops",
    addresses.TREASURY_VAULT: "Badger Treasury Vault",
    addresses.IBBTC_Y_PEAK: "IBBTC ywBTC Peak",
}

REWARDS_BLACKLIST = {
    addresses.CREAM_BBADGER: "Cream bBadger",
    addresses.SUSHI_BBADGER_WETH: "Sushiswap bBadger/Weth",
    addresses.BBADGER: "Badger Vault",
    addresses.BADGER_PAYMENTS: "Badger Payments",
}

STAKE_RATIO_RANGES = list(
    [
        (0, 1),
        (0.001, 2),
        (0.0025, 5),
        (0.005, 10),
        (0.01, 20),
        (0.025, 50),
        (0.05, 100),
        (0.075, 150),
        (0.10, 200),
        (0.15, 300),
        (0.2, 400),
        (0.25, 500),
        (0.3, 600),
        (0.4, 800),
        (0.5, 1000),
        (0.6, 1200),
        (0.7, 1400),
        (0.8, 1600),
        (0.9, 1800),
        (1, 2000),
    ]
)

LP_SETT_INFO = {"type": "native", "ratio": 0.5}
TOKEN_SETT_INFO = {"type": "native", "ratio": 1}

NATIVE = [
    # ethereum
    addresses.BBADGER,
    addresses.BUNI_BADGER_WBTC,
    addresses.BSLP_BADGER_WBTC,
    addresses.BDIGG,
    addresses.BUNI_DIGG_WBTC,
    addresses.BSLP_DIGG_WBTC,
    addresses.REM_BADGER,
    addresses.REM_DIGG,
    # arbitrum
    addresses.ARB_BSWAPR_WETH_BADGER,
]

DISABLED_VAULTS = [
    addresses.BSC_TEST_VAULT,
    # arbitrum
    addresses.ARB_REWARDS_LOGGER,
    addresses.ARB_BCRV_TRICRYPTO_LIGHT,
    addresses.ARB_BSWAPR_WETH_WBTC,
    addresses.ARB_BSWAPR_WETH_SWAPR,
    # ethereum
    addresses.BCRV_TRICRYPTO_1,
    addresses.BHARVEST_REN_WBTC,
]

PRO_RATA_VAULTS = [
    addresses.BVECVX,
    addresses.BVECVX_CVX_LP_SETT,
]

DIGG_SETTS = [addresses.BDIGG, addresses.REM_DIGG]

BOOST_CHAINS = [Network.Ethereum, Network.Polygon, Network.Arbitrum]

SANITY_TOKEN_AMOUNT = 4000 * 1e18
BOOST_BLOCK_DELAY = 10

NUMBER_OF_HISTORICAL_SNAPSHOTS_FOR_TREE_REWARDS = 3
NUMBER_OF_HISTORICAL_SNAPSHOTS_FOR_SETT_REWARDS = 2

# accepting distributions within 1% of expected values, REWARD_ERROR_TOLERANCE = 0.01
REWARD_ERROR_TOLERANCE = 0.01

ZERO_CYCLE = 0
