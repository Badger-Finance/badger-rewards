from enum import Enum


class Network(str, Enum):
    Ethereum = "ethereum"
    Polygon = "polygon"
    Arbitrum = "arbitrum"
    BinanceSmartChain = "binancesmartchain"
    Avalanche = "avalanche"
    Fantom = "fantom"
    xDai = "xdai"

    def __str__(self):
        return self.value


class BalanceType(str, Enum):
    Native = "native"
    NonNative = "non_native"
    Excluded = "excluded"

    def __str__(self):
        return self.value


class Environment(str, Enum):
    Test = "test"
    Staging = "stg"
    Production = "prod"

    def __str__(self):
        return self.value


class BotType(str, Enum):
    Cycle = "cycle"
    Boost = "boost"

    def __str__(self):
        return self.value


class BucketType(str, Enum):
    Merkle = "merkle"
    Json = "json"

    def __str__(self):
        return self.value


class Abi(str, Enum):
    ERC20 = "ERC20"
    Digg = "Digg"
    BadgerTree = "BadgerTreeV2"
    ChainlinkOracle = "ChainlinkOracle"
    RewardsLogger = "RewardsLogger"
    EmissionControl = "EmissionControl"
    NFTControl = "NFTControl"
    Strategy = "BaseStrategy"
    Controller = "Controller"
    CErc20Delegator = "CErc20Delegator"

    def __str__(self) -> str:
        return self.value

class DiscordRoles(str, Enum):
    RewardsPod = "<@&804147406043086850>"

    def __str__(self) -> str:
        return self.value
