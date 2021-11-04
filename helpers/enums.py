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
