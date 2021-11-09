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
