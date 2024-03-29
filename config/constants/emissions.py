import datetime
import config.constants.addresses as addresses
from helpers.enums import Network

SCHEDULE_REWARDS_BLACKLIST = {
    addresses.DEV_MULTISIG: "Badger Dev Multisig",
    addresses.TECH_OPS: "Badger Tech Ops",
    addresses.TREASURY_OPS: "Badger Treasury Ops",
    addresses.TREASURY_VAULT: "Badger Treasury Vault",
    addresses.IBBTC_Y_PEAK: "IBBTC ywBTC Peak",
    addresses.BALANCER_VAULT: "Balancer Vault",
}

TREE_REWARDS_BLACKLIST = {
    addresses.CREAM_BBADGER: "Cream bBadger",
    addresses.SUSHI_BBADGER_WETH: "Sushiswap bBadger/Weth",
    addresses.BBADGER: "Badger Vault",
    addresses.BALANCER_VAULT: "Balancer Vault",
}

BVECVX_VOTER_BLACKLIST = {addresses.BVECVX_VOTER: "Badger bveCVX Voter"}
DIGG_BOOST_VAULTS = [
    addresses.BDIGG,
    addresses.BSLP_DIGG_WBTC,
    addresses.BUNI_DIGG_WBTC,
    addresses.BAURA_DIGG_WBTC,
]

NATIVE_TOKEN_REWARDS = {Network.Ethereum: [addresses.BADGER, addresses.DIGG]}

BVECVX_VOTER_BLACKLIST_TOKENS = {Network.Ethereum: [addresses.BVECVX, addresses.BADGER]}

BVECVX_BOOST_WEIGHT = 0.5
DIGG_BOOST_WEIGHT = 1

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
    addresses.REM_BADGER,
    addresses.BCRV_BADGER_WBTC,
    addresses.BAURA_BADGER_WBTC,
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
    addresses.BUNI_BADGER_WBTC,
]

NO_BOOST_VAULTS = [
    addresses.BVECVX,
    addresses.BVECVX_CVX_LP_SETT,
    addresses.BDIGG,
    addresses.BSLP_DIGG_WBTC,
    addresses.BUNI_DIGG_WBTC,
    addresses.REM_DIGG,
]

DIGG_SETTS = [addresses.BDIGG, addresses.REM_DIGG]

BOOST_CHAINS = [Network.Ethereum, Network.Polygon, Network.Arbitrum]

MAX_BOOST = 3000

SANITY_TOKEN_AMOUNT = 4000 * 1e18

NUMBER_OF_HISTORICAL_SNAPSHOTS_FOR_TREE_REWARDS = 3
NUMBER_OF_HISTORICAL_SNAPSHOTS_FOR_SETT_REWARDS = 2

# accepting distributions within 1% of expected values, REWARD_ERROR_TOLERANCE = 0.01
REWARD_ERROR_TOLERANCE = 0.01

ZERO_CYCLE = 0

NO_BOOST_CHAINS = [Network.Fantom]

FUSE_TOKEN_INFO = {
    addresses.BADGER: {
        "underlying": addresses.BADGER,
        "symbol": "fBADGER-22",
        "contract": addresses.FBADGER,
    },
    addresses.DIGG: {
        "underlying": addresses.DIGG,
        "symbol": "fDIGG-22",
        "contract": addresses.FDIGG,
    },
    addresses.BVECVX: {
        "underlying": addresses.BVECVX,
        "symbol": "fbveCVX-22",
        "contract": addresses.FBVECVX,
    },
}
FUSE_MANTISSA = 18
FUSE_TOKEN_BASE = 10
FTOKEN_DECIMALS = 8

NOW = datetime.date.today()

# Boost for Standard Councilors increases 115 per month
STANDARD_COUNCILOR_BOOST = 115
# Boost for Committee Councilors increases 430 per month + standard
COMMITEE_COUNCILOR_BOOST = 430 + STANDARD_COUNCILOR_BOOST

COUNCILOR_MONTHS_ACCRUED = {
    "0xD798428e860465E08B522f8440f707593E6d22C6": (NOW - datetime.date(2022, 7, 1)).days // 30,
    "0xc9049cB9aB542D0Bd0fA099ff8E3e8b3FCa13b13": (NOW - datetime.date(2022, 7, 1)).days // 30,
    "0xB5c46131B4d8d13e4c0E476B9A2Ea5b43945891e": (NOW - datetime.date(2022, 7, 1)).days // 30,
    "0x567244C8E8dff152bE7A276DCD05AA332767386E": (NOW - datetime.date(2022, 7, 1)).days // 30,
}

COUNCILOR_RATE = {
    "0xD798428e860465E08B522f8440f707593E6d22C6": STANDARD_COUNCILOR_BOOST,
    "0xc9049cB9aB542D0Bd0fA099ff8E3e8b3FCa13b13": COMMITEE_COUNCILOR_BOOST,
    "0xB5c46131B4d8d13e4c0E476B9A2Ea5b43945891e": STANDARD_COUNCILOR_BOOST,
    "0x567244C8E8dff152bE7A276DCD05AA332767386E": STANDARD_COUNCILOR_BOOST,
}

CONTRIBUTOR_BOOST = {
    Network.Ethereum: {
        councilor: COUNCILOR_MONTHS_ACCRUED[councilor] * COUNCILOR_RATE[councilor]
        for councilor in COUNCILOR_MONTHS_ACCRUED
    }
}

# March 31, 2023 23:59:59 - End of next council ratification
CONTRIBUTOR_BOOST_END_TIMESTAMP = 1680321599
