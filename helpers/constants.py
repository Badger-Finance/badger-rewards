from dotmap import DotMap
from web3 import Web3

from helpers.enums import BalanceType, BotType, BucketType, Environment, Network

AddressZero = "0x0000000000000000000000000000000000000000"
MaxUint256 = str(int(2 ** 256 - 1))
EmptyBytes32 = "0x0000000000000000000000000000000000000000000000000000000000000000"

DEFAULT_ADMIN_ROLE = (
    "0x0000000000000000000000000000000000000000000000000000000000000000"
)


class RoleRegistry:
    def __init__(self):
        self.roles = {}

    def add_role(self, name):
        encoded = Web3.keccak(text=name).hex()
        self.roles[name] = encoded


# Approved Contract Roles
APPROVED_STAKER_ROLE = Web3.keccak(text="APPROVED_STAKER_ROLE").hex()
APPROVED_SETT_ROLE = Web3.keccak(text="APPROVED_SETT_ROLE").hex()
APPROVED_STRATEGY_ROLE = Web3.keccak(text="APPROVED_STRATEGY_ROLE").hex()

PAUSER_ROLE = Web3.keccak(text="PAUSER_ROLE").hex()
UNPAUSER_ROLE = Web3.keccak(text="UNPAUSER_ROLE").hex()
GUARDIAN_ROLE = Web3.keccak(text="GUARDIAN_ROLE").hex()

# BadgerTree Roles
ROOT_UPDATER_ROLE = Web3.keccak(text="ROOT_UPDATER_ROLE").hex()
ROOT_PROPOSER_ROLE = Web3.keccak(text="ROOT_PROPOSER_ROLE").hex()
ROOT_VALIDATOR_ROLE = Web3.keccak(text="ROOT_VALIDATOR_ROLE").hex()

# UnlockSchedule Roles
TOKEN_LOCKER_ROLE = Web3.keccak(text="TOKEN_LOCKER_ROLE").hex()

# Keeper Roles
KEEPER_ROLE = Web3.keccak(text="KEEPER_ROLE").hex()
EARNER_ROLE = Web3.keccak(text="EARNER_ROLE").hex()

# External Harvester Roles
SWAPPER_ROLE = Web3.keccak(text="SWAPPER_ROLE").hex()
DISTRIBUTOR_ROLE = Web3.keccak(text="DISTRIBUTOR_ROLE").hex()

APPROVED_ACCOUNT_ROLE = Web3.keccak(text="APPROVED_ACCOUNT_ROLE").hex()

role_registry = RoleRegistry()

role_registry.add_role("APPROVED_STAKER_ROLE")
role_registry.add_role("APPROVED_SETT_ROLE")
role_registry.add_role("APPROVED_STRATEGY_ROLE")

role_registry.add_role("PAUSER_ROLE")
role_registry.add_role("UNPAUSER_ROLE")
role_registry.add_role("GUARDIAN_ROLE")

role_registry.add_role("ROOT_UPDATER_ROLE")
role_registry.add_role("ROOT_PROPOSER_ROLE")
role_registry.add_role("ROOT_VALIDATOR_ROLE")

role_registry.add_role("TOKEN_LOCKER_ROLE")

role_registry.add_role("KEEPER_ROLE")
role_registry.add_role("EARNER_ROLE")

role_registry.add_role("SWAPPER_ROLE")
role_registry.add_role("DISTRIBUTOR_ROLE")

role_registry.add_role("APPROVED_ACCOUNT_ROLE")


DEV_MULTISIG = "0xB65cef03b9B89f99517643226d76e286ee999e77"
TECH_OPS = "0x86cbD0ce0c087b482782c181dA8d191De18C8275"
TREASURY_OPS = "0x042B32Ac6b453485e357938bdC38e0340d4b9276"
TREASURY_VAULT = "0xD0A7A8B98957b9CD3cFB9c0425AbE44551158e9e"

CREAM_BBADGER = "0x8B950f43fCAc4931D408F1fcdA55C6CB6cbF3096"
SUSHI_BBADGER_WETH = "0x0a54d4b378C8dBfC7bC93BE50C85DebAFdb87439"

ETH_BADGER_TREE = "0x660802Fc641b154aBA66a62137e71f331B6d787A"
IBBTC_PEAK = "0x41671BA1abcbA387b9b2B752c205e22e916BE6e3"
IBBTC_Y_PEAK = "0x825218beD8BE0B30be39475755AceE0250C50627"
IBBTC_MULTISIG = "0xB76782B51BFf9C27bA69C77027e20Abd92Bcf3a8"
BADGER_PAYMENTS = "0xD4868d98849a58F743787c77738D808376210292"


ETH_REWARDS_LOGGER = "0x0A4F4e92C3334821EbB523324D09E321a6B0d8ec"
ETH_GAS_ORACLE = "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"
ETH_EMISSION_CONTROL = "0x31825c0A6278b89338970e3eB979b05B27FAa263"
ETH_NFT_CONTROL = "0xe1AaC4bE0FCF218533c95808BB638f4D727E5714"

POLY_BADGER_TREE = "0x2C798FaFd37C7DCdcAc2498e19432898Bc51376b"
POLY_REWARDS_LOGGER = "0xd0EE2A5108b8800D688AbC834445fd03b3b2738e"
POLY_GAS_ORACLE = "0xAB594600376Ec9fD91F8e885dADF0CE036862dE0"

ARB_BADGER_TREE = "0x635EB2C39C75954bb53Ebc011BDC6AfAAcE115A6"
ARB_REWARDS_LOGGER = "0x85E1cACAe9a63429394d68Db59E14af74143c61c"
ARB_GAS_ORACLE = "0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612"
ARB_EMISSION_CONTROL = "0x78418681f9eD228D627F785Fb9607Ed5175518Fd"

DIGG = "0x798D1bE841a82a273720CE31c822C61a67a601C3"
BADGER = "0x3472A5A71965499acd81997a54BBA8D852C6E53d"
FARM = "0xa0246c9032bC3A600820415aE600c6388619A14D"
XSUSHI = "0x8798249c2E607446EfB7Ad49eC89dD1865Ff4272"
DFD = "0x20c36f062a31865bED8a5B1e512D9a1A20AA333A"
BVECVX_CVX_LP = "0x04c90C198b2eFF55716079bc06d7CCc4aa4d7512"

BIBBTC_CURVE_LP = "0xaE96fF08771a109dc6650a1BdCa62F2d558E40af"
PNT = "0x89Ab32156e46F46D02ade3FEcbe5Fc4243B9AAeD"
BOR = "0x3c9d6c1C73b31c837832c72E04D3152f051fc1A9"

ARB_BADGER = "0xBfa641051Ba0a0Ad1b0AcF549a89536A0D76472E"
ARB_CRV = "0x11cDb42B0EB46D95f990BeDD4695A6e3fA034978"

POLY_BADGER = "0x1FcbE5937B0cc2adf69772D228fA4205aCF4D9b2"
POLY_SUSHI = "0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a"

BSC_TEST_VAULT = "0xB6bd5ae3d5F78A6Bb04bBb031E24fA9C2BbD090d"

BBADGER_ADDRESS = "0x19D97D8fA813EE2f51aD4B4e04EA08bAf4DFfC28"
YEARN_WBTC_ADDRESS = "0x4b92d19c11435614CD49Af1b589001b7c08cD4D5"
CVX_CRV_ADDRESS = "0x2B5455aac8d64C14786c3a29858E43b5945819C0"
SWAPR_WETH_SWAPR_ARB_ADDRESS = "0x0c2153e8aE4DB8233c61717cDC4c75630E952561"

SETTS = {
    Network.Ethereum: {
        "badger": BBADGER_ADDRESS,
        "ren_crv": "0x6dEf55d2e18486B9dDfaA075bc4e4EE0B28c1545",
        "rem_badger": "0x6aF7377b5009d7d154F36FE9e235aE1DA27Aea22",
        "sbtc_crv": "0xd04c48A53c111300aD41190D63681ed3dAd998eC",
        "tbtc_crv": "0xb9D076fDe463dbc9f915E5392F807315Bf940334",
        "uni_badger_wbtc": "0x235c9e24D3FB2FAFd58a2E49D454Fdcd2DBf7FF1",
        "harvest_ren_crv": "0xAf5A1DECfa95BAF63E0084a35c62592B774A2A87",
        "sushi_wbtc_eth": "0x758A43EE2BFf8230eeb784879CdcFF4828F2544D",
        "sushi_badger_wbtc": "0x1862A18181346EBd9EdAf800804f89190DeF24a5",
        "digg": "0x7e7E112A68d8D2E221E11047a72fFC1065c38e1a",
        "uni_digg_wbtc": "0xC17078FDd324CC473F8175Dc5290fae5f2E84714",
        "sushi_digg_wbtc": "0x88128580ACdD9c04Ce47AFcE196875747bF2A9f6",
        "yearn_wbtc": YEARN_WBTC_ADDRESS,
        "sushi_ibbtc_wbtc": "0x8a8FFec8f4A0C8c9585Da95D9D97e8Cd6de273DE",
        "experimental_digg": "0x608b6D82eb121F3e5C0baeeD32d81007B916E83C",
        "hbtc_crv": "0x8c76970747afd5398e958bDfadA4cf0B9FcA16c4",
        "pbtc_crv": "0x55912D0Cf83B75c492E761932ABc4DB4a5CB1b17",
        "obtc_crv": "0xf349c0faA80fC1870306Ac093f75934078e28991",
        "bbtc_crv": "0x5Dce29e92b1b939F8E8C60DcF15BDE82A85be4a9",
        "cvx_crv": CVX_CRV_ADDRESS,
        "cvx": "0x53C8E199eb2Cb7c01543C137078a038937a68E40",
        "renbtc": "0x58CAc1409F1ffbdcBA6a58d54c94CAC3fb4C6F8B",
        "tricrypto_crv": "0xBE08Ef12e4a553666291E9fFC24fCCFd354F2Dd2",
        "tricrypto2_crv": "0x27E98fC7d05f54E544d16F58C194C2D7ba71e3B5",
        "imbtc": "0x599D92B453C010b1050d31C364f6ee17E819f193",
        "mstable_fp_mbtc_hbtc": "0x26B8efa69603537AC8ab55768b6740b67664D518",
        "bvecvx": "0xfd05D3C7fe2924020620A8bE4961bBaA747e6305",
        "bvecvx_cvx": "0x937B8E917d0F36eDEBBA8E459C5FB16F3b315551",
        "ibbtc_crv": "0xaE96fF08771a109dc6650a1BdCa62F2d558E40af",
    },
    Network.Arbitrum: {
        "sushi_weth_sushi": "0xe774D1FB3133b037AA17D39165b8F45f444f632d",
        "sushi_weth_wbtc": "0xFc13209cAfE8fb3bb5fbD929eC9F11a39e8Ac041",
        "crv_wbtc_ren": "0xBA418CDdd91111F5c1D1Ac2777Fa8CEa28D71843",
        "tricrypto": "0x4591890225394BF66044347653e112621AF7DDeb",
        "swapr_weth_swapr": "0x0c2153e8aE4DB8233c61717cDC4c75630E952561",
        "tricrypto_light": "0xfdb9e5a186FB7655aC9cD7CAFF3d6D4c6064cc50",
        "swapr_weth_wbtc": "0xaf9aB64F568149361ab670372b16661f4380e80B",
        "swapr_weth_badger": "0xE9C12F06F8AFFD8719263FE4a81671453220389c",
        "swapr_weth_ibbtc": "0x60129B2b762952Dfe8b21f40ee8aa3B2A4623546",
    },
    Network.Polygon: {
        "sushi_ibbtc_wbtc": "0xEa8567d84E3e54B32176418B4e0C736b56378961",
        "qlp_wbtc_usdc": "0x6B2d4c4bb50274c5D4986Ff678cC971c0260E967",
        "tricrypto": "0x85E1cACAe9a63429394d68Db59E14af74143c61c",
        "crv_wbtc_renbtc": "0x7B6bfB88904e4B3A6d239d5Ed8adF557B22C10FC",
    },
}


TOKENS_TO_CHECK = {
    Network.Ethereum: {
        "Badger": BADGER,
        "Digg": DIGG,
        "xSushi": XSUSHI,
        "Dfd": DFD,
        "bCvxCrv": SETTS[Network.Ethereum]["cvx_crv"],
        "bCvx": SETTS[Network.Ethereum]["cvx"],
        "bveCVX": SETTS[Network.Ethereum]["bvecvx"],
    },
    Network.Arbitrum: {
        "Badger": ARB_BADGER,
        "Crv": ARB_CRV,
        "Sushi/WETH LP": SETTS[Network.Arbitrum]["sushi_weth_sushi"],
        "Swapr/WETH LP": SETTS[Network.Arbitrum]["swapr_weth_swapr"],
    },
    Network.Polygon: {
        "Badger": POLY_BADGER,
        "Sushi": POLY_SUSHI,
    },
}

EMISSIONS_BLACKLIST = {
    DEV_MULTISIG: "Badger Dev Multisig",
    TECH_OPS: "Badger Tech Ops",
    TREASURY_OPS: "Badger Treasury Ops",
    TREASURY_VAULT: "Badger Treasury Vault",
    IBBTC_Y_PEAK: "IBBTC ywBTC Peak",
}

REWARDS_BLACKLIST = {
    CREAM_BBADGER: "Cream bBadger",
    SUSHI_BBADGER_WETH: "Sushiswap bBadger/Weth",
    SETTS[Network.Ethereum]["badger"]: "Badger Vault",
    BADGER_PAYMENTS: "Badger Payments",
    BVECVX_CVX_LP: "Curve bveCVX/CVX",
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
    SETTS[Network.Ethereum]["badger"],
    SETTS[Network.Ethereum]["uni_badger_wbtc"],
    SETTS[Network.Ethereum]["sushi_badger_wbtc"],
    SETTS[Network.Ethereum]["digg"],
    SETTS[Network.Ethereum]["uni_digg_wbtc"],
    SETTS[Network.Ethereum]["sushi_digg_wbtc"],
    SETTS[Network.Ethereum]["rem_badger"],
    SETTS[Network.Arbitrum]["swapr_weth_badger"],
]

EMISSIONS_CONTRACTS = {
    Network.Ethereum: DotMap(
        {
            "EmissionControl": ETH_EMISSION_CONTROL,
            "BadgerTree": ETH_BADGER_TREE,
            "RewardsLogger": ETH_REWARDS_LOGGER,
            "GasOracle": ETH_GAS_ORACLE,
            "NFTControl": ETH_NFT_CONTROL,
        }
    ),
    Network.Polygon: DotMap(
        {
            "BadgerTree": POLY_BADGER_TREE,
            "RewardsLogger": POLY_REWARDS_LOGGER,
            "GasOracle": POLY_GAS_ORACLE,
        }
    ),
    Network.Arbitrum: DotMap(
        {
            "EmissionControl": ARB_EMISSION_CONTROL,
            "BadgerTree": ARB_BADGER_TREE,
            "RewardsLogger": ARB_REWARDS_LOGGER,
            "GasOracle": ARB_GAS_ORACLE,
        }
    ),
}

DISABLED_VAULTS = [
    BSC_TEST_VAULT,
    ARB_REWARDS_LOGGER,
    SETTS[Network.Arbitrum]["tricrypto_light"],
    SETTS[Network.Arbitrum]["swapr_weth_wbtc"],
    SETTS[Network.Arbitrum]["swapr_weth_swapr"],
    SETTS[Network.Ethereum]["tricrypto_crv"],
    SETTS[Network.Ethereum]["harvest_ren_crv"],
]
PRO_RATA_VAULTS = [
    SETTS[Network.Ethereum]["bvecvx"],
    SETTS[Network.Ethereum]["bvecvx_cvx"],
]

MONITORING_SECRET_NAMES = {
    Environment.Production: {
        Network.Ethereum: {
            BotType.Cycle: "cycle-bot/eth/prod-discord-url",
            BotType.Boost: "boost-bot/eth/prod-discord-url",
        },
        Network.Polygon: {
            BotType.Cycle: "cycle-bot/prod-discord-url",
            BotType.Boost: "boost-bot/polygon/prod-discord-url",
        },
        Network.Arbitrum: {
            BotType.Cycle: "cycle-bot/arbitrum/prod-discord-url",
            BotType.Boost: "boost-bot/arbitrum/prod-discord-url",
        },
    },
    Environment.Staging: {
        Network.Ethereum: {
            BotType.Cycle: "cycle-bot/test-discord-url",
            BotType.Boost: "boost-bot/eth/staging-discord-url",
        },
        Network.Polygon: {
            BotType.Cycle: "cycle-bot/test-discord-url",
            BotType.Boost: "boost-bot/polygon/staging-discord-url",
        },
        Network.Arbitrum: {
            BotType.Cycle: "cycle-bot/test-discord-url",
            BotType.Boost: "boost-bot/arbitrum/staging-discord-url",
        },
    },
    Environment.Test: {
        Network.Ethereum: {
            BotType.Cycle: "cycle-bot/test-discord-url",
            BotType.Boost: "boost-bot/test-discord-url",
        },
        Network.Polygon: {
            BotType.Cycle: "cycle-bot/test-discord-url",
            BotType.Boost: "boost-bot/test-discord-url",
        },
        Network.Arbitrum: {
            BotType.Cycle: "cycle-bot/test-discord-url",
            BotType.Boost: "boost-bot/test-discord-url",
        },
    },
}

BOOST_CHAINS = [Network.Ethereum, Network.Polygon, Network.Arbitrum]

CHAIN_IDS = {
    Network.Ethereum: 1,
    Network.Arbitrum: 42161,
    Network.Polygon: 137,
}

NETWORK_TO_BADGER_TOKEN = {
    Network.Ethereum: BADGER,
    Network.Polygon: POLY_BADGER,
    Network.Arbitrum: ARB_BADGER,
}

S3_BUCKETS = {
    BucketType.Merkle: {
        Environment.Staging: "badger-staging-merkle-proofs",
        Environment.Production: "badger-merkle-proofs",
    }
}

CLAIMABLE_TOKENS = {
    Network.Ethereum: {
        BalanceType.Native: [BADGER, DIGG],
        BalanceType.NonNative: [SETTS[Network.Ethereum]["cvx_crv"]],
    },
    Network.Arbitrum: {BalanceType.Native: [ARB_BADGER], BalanceType.NonNative: []},
    Network.Polygon: {BalanceType.Native: [POLY_BADGER], BalanceType.NonNative: []},
}

UNCLAIMED_REWARDS_TOKENS = {
    Network.Ethereum: [SETTS[Network.Ethereum]["cvx_crv"], SETTS[Network.Ethereum]["bvecvx"]]
}
BOOSTED_EMISSION_TOKENS = {
    Network.Ethereum: [BADGER, DIGG],
    Network.Arbitrum: [ARB_BADGER],
}

ABI_DIRS = {
    Network.Ethereum: "eth",
    Network.Polygon: "polygon",
    Network.Arbitrum: "arbitrum",
}

SANITY_TOKEN_AMOUNT = 4000 * 1e18
BOOST_BLOCK_DELAY = 10


DECIMAL_MAPPING = {
    Network.Ethereum: 1e18,
    Network.Polygon: 1e18,
    Network.Arbitrum: 1e18,
}

NUMBER_OF_HISTORICAL_SNAPSHOTS_FOR_TREE_REWARDS = 3
NUMBER_OF_HISTORICAL_SNAPSHOTS_FOR_SETT_REWARDS = 2
ZERO_CYCLE = 0

# OK with token distributions being within 1% of expected values
REWARD_ERROR_TOLERANCE = .01
