from helpers.enums import (
    Environment,
    Network,
)

subgraph_urls = {
    Environment.Production: {
        # Chain graphs
        Network.BinanceSmartChain: (
            "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-bsc"
        ),
        Network.Ethereum: "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts",
        Network.Polygon: (
            "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-polygon"
        ),
        Network.Arbitrum: (
            "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-arbitrum"
        ),
        Network.Fantom: (
            "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-fantom"
        ),
        # Token graphs
        f"tokens-{Network.Ethereum}": (
            "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens"
        ),
        f"tokens-{Network.BinanceSmartChain}": (
            "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens-bsc"
        ),
        f"tokens-{Network.Polygon}": (
            "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens-polygon"
        ),
        f"tokens-{Network.Arbitrum}": (
            "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens-arbitrum"
        ),
        f"tokens-{Network.Fantom}": (
            "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens-fantom"
        ),
        "fuse": "https://api.thegraph.com/subgraphs/name/badger-finance/fuse-subgraph",
        "thegraph": "https://api.thegraph.com/index-node/graphql",
        "nfts": "https://api.thegraph.com/subgraphs/name/badger-finance/badger-nfts",
        "across": "https://api.thegraph.com/subgraphs/name/badger-finance/badger-across"
    },
    Environment.Staging: {
    }
}
