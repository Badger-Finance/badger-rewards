from dotmap import DotMap

import config.constants.addresses as addresses
from helpers.enums import BalanceType, Network

SETTS = {
    Network.Ethereum: {
        "badger": addresses.BBADGER,
        "ren_crv": addresses.BCRV_REN_WBTC,
        "rem_badger": addresses.REM_BADGER,
        "sbtc_crv": addresses.BCRV_SBTC,
        "tbtc_crv": addresses.BCRV_TBTC,
        "uni_badger_wbtc": addresses.BUNI_BADGER_WBTC,
        "harvest_ren_crv": addresses.BHARVEST_REN_WBTC,
        "sushi_wbtc_eth": addresses.BSLP_WBTC_ETH,
        "sushi_badger_wbtc": addresses.BSLP_BADGER_WBTC,
        "badger_wbtc_crv": addresses.BCRV_BADGER_WBTC,
        "digg": addresses.BDIGG,
        "uni_digg_wbtc": addresses.BUNI_DIGG_WBTC,
        "sushi_digg_wbtc": addresses.BSLP_DIGG_WBTC,
        "yearn_wbtc": addresses.BYWBTC,
        "sushi_ibbtc_wbtc": addresses.BSLP_IBBTC_WBTC,
        "experimental_digg": addresses.BDIGG_STABILITY,
        "hbtc_crv": addresses.BCRV_HBTC,
        "pbtc_crv": addresses.BCRV_PBTC,
        "obtc_crv": addresses.BCRV_OBTC,
        "bbtc_crv": addresses.BCRV_BBTC,
        "cvx_crv": addresses.BCVXCRV,
        "cvx": addresses.BCVX,
        "tricrypto_crv": addresses.BCRV_TRICRYPTO_1,
        "tricrypto2_crv": addresses.BCRV_TRICRYPTO_2,
        "imbtc": addresses.BIMBTC,
        "mstable_fp_mbtc_hbtc": addresses.BMBTC_HBTC,
        "bvecvx": addresses.BVECVX,
        "bvecvx_cvx": addresses.BVECVX_CVX_LP_SETT,
        "ibbtc_crv": addresses.BCRV_IBBTC,
        "rem_digg": addresses.REM_DIGG
    },
    Network.Arbitrum: {
        "sushi_weth_sushi": addresses.ARB_BSLP_WETH_SUSHI,
        "sushi_weth_wbtc": addresses.ARB_BSLP_WETH_WBTC,
        "crv_wbtc_ren": addresses.ARB_BCRV_WBTC_REN,
        "tricrypto": addresses.ARB_BCRV_TRICRYPTO,
        "swapr_weth_swapr": addresses.ARB_BSWAPR_WETH_SWAPR,
        "tricrypto_light": addresses.ARB_BCRV_TRICRYPTO_LIGHT,
        "swapr_weth_wbtc": addresses.ARB_BSWAPR_WETH_WBTC,
        "swapr_weth_badger": addresses.ARB_BSWAPR_WETH_BADGER,
        "swapr_weth_ibbtc": addresses.ARB_BSWAPR_WETH_IBBTC,
    },
    Network.Polygon: {
        "sushi_ibbtc_wbtc": addresses.POLY_BSLP_IBBTC_WBTC,
        "qlp_wbtc_usdc": addresses.POLY_BQLP_WBTC_USDC,
        "tricrypto": addresses.POLY_BCRV_TRICRYPTO,
        "crv_wbtc_renbtc": addresses.POLY_BCRV_RENBTC_WBTC,
    },
    Network.Fantom: {
        "smm_usdc_dai": addresses.FTM_BSMM_USDC_DAI
    }
}

TOKENS_TO_CHECK = {
    Network.Ethereum: {
        "Badger": addresses.BADGER,
        "Digg": addresses.DIGG,
        "xSushi": addresses.XSUSHI,
        "Dfd": addresses.DFD,
        "bCvxCrv": addresses.BCVXCRV,
        "bCvx": addresses.BCVX,
        "bveCVX": addresses.BVECVX,
    },
    Network.Arbitrum: {
        "Badger": addresses.ARB_BADGER,
        "Crv": addresses.ARB_CRV,
        "Sushi/WETH LP": addresses.ARB_BSLP_WETH_SUSHI,
        "Swapr/WETH LP": addresses.ARB_BSWAPR_WETH_SWAPR,
    },
    Network.Polygon: {
        "Badger": addresses.POLY_BADGER,
        "Sushi": addresses.POLY_SUSHI,
    },
    Network.Fantom: {
        "Solidly": addresses.FTM_SOLIDLY,
    }
}

EMISSIONS_CONTRACTS = {
    Network.Ethereum: DotMap(
        {
            "EmissionControl": addresses.ETH_EMISSION_CONTROL,
            "BadgerTree": addresses.ETH_BADGER_TREE,
            "RewardsLogger": addresses.ETH_REWARDS_LOGGER,
            "GasOracle": addresses.ETH_GAS_ORACLE,
            "NFTControl": addresses.ETH_NFT_CONTROL,
        }
    ),
    Network.Polygon: DotMap(
        {
            "BadgerTree": addresses.POLY_BADGER_TREE,
            "RewardsLogger": addresses.POLY_REWARDS_LOGGER,
            "GasOracle": addresses.POLY_GAS_ORACLE,
        }
    ),
    Network.Arbitrum: DotMap(
        {
            "EmissionControl": addresses.ARB_EMISSION_CONTROL,
            "BadgerTree": addresses.ARB_BADGER_TREE,
            "RewardsLogger": addresses.ARB_REWARDS_LOGGER,
            "GasOracle": addresses.ARB_GAS_ORACLE,
        }
    ),
    Network.Fantom: DotMap(
        {
            "BadgerTree": addresses.FTM_BADGER_TREE,
            "RewardsLogger": addresses.FTM_REWARDS_LOGGER,
            "GasOracle": addresses.FTM_GAS_ORACLE
        }
    )
}

CHAIN_IDS = {
    Network.Ethereum: 1,
    Network.Arbitrum: 42161,
    Network.Polygon: 137,
    Network.Fantom: 250
}

NETWORK_TO_BADGER_TOKEN = {
    Network.Ethereum: addresses.BADGER,
    Network.Polygon: addresses.POLY_BADGER,
    Network.Arbitrum: addresses.ARB_BADGER,
    Network.Fantom: addresses.FTM_BADGER
}

CLAIMABLE_TOKENS = {
    Network.Ethereum: {
        BalanceType.Native: [addresses.BADGER],
        BalanceType.NonNative: [addresses.BCVXCRV],
    },
    Network.Arbitrum: {BalanceType.Native: [addresses.ARB_BADGER], BalanceType.NonNative: []},
    Network.Polygon: {BalanceType.Native: [addresses.POLY_BADGER], BalanceType.NonNative: []},
    Network.Fantom: {
        BalanceType.Native: [],
        BalanceType.NonNative: [addresses.FTM_SOLIDLY]
    }
}

UNCLAIMED_REWARDS_TOKENS = {
    Network.Ethereum: [addresses.BCVXCRV, addresses.BVECVX]
}

BOOSTED_EMISSION_TOKENS = {
    Network.Ethereum: [addresses.BADGER, addresses.DIGG],
    Network.Arbitrum: [addresses.ARB_BADGER],
}

ABI_DIRS = {
    Network.Ethereum: "eth",
    Network.Polygon: "polygon",
    Network.Arbitrum: "arbitrum",
    Network.Fantom: "fantom"
}

DECIMAL_MAPPING = {
    Network.Ethereum: 1e18,
    Network.Polygon: 1e18,
    Network.Arbitrum: 1e18,
    Network.Fantom: 1e18
}

TREE_ACTION_GAS = {
    Network.Ethereum: 200000,
    Network.Arbitrum: 3000000
}

CHAIN_EXPLORER_URLS = {
    Network.Ethereum: "etherscan.io",
    Network.Polygon: "polygonscan.com",
    Network.Arbitrum: "arbiscan.io",
    Network.Fantom: "ftmscan.com"
}

BOOST_BUFFER = {
    Network.Arbitrum: 1000
}
