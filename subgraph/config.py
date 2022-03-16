from helpers.enums import (
    Environment,
    Network,
)

subgraph_urls = {
    Environment.Production: {
        # Chain graphs
        Network.BinanceSmartChain: (
            "https://api.thegraph.com/subgraphs/name/axejintao/badger-dao-bsc"
        ),
        Network.Ethereum: "https://api.thegraph.com/subgraphs/name/axejintao/badger-dao",
        Network.Polygon: "https://api.thegraph.com/subgraphs/name/axejintao/badger-dao-polygon",
        Network.Arbitrum: "https://api.thegraph.com/subgraphs/name/axejintao/badger-dao-arbitrum",
        Network.Fantom: (
            "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-fantom"
        ),
        Network.xDai: "https://api.thegraph.com/subgraphs/name/axejintao/badger-dao-xdai",
        # Token graphs
        f"tokens-{Network.Ethereum}": (
            "https://api.thegraph.com/subgraphs/name/darruma/badger-tokens"
        ),
        f"tokens-{Network.BinanceSmartChain}": (
            "https://bgraph-bsc.badger.guru/subgraphs/name/swole/badger-subgraph"
        ),
        f"tokens-{Network.Polygon}": (
            "https://api.thegraph.com/subgraphs/name/darruma/badger-tokens-polygon"
        ),
        f"tokens-{Network.Arbitrum}": (
            "https://api.thegraph.com/subgraphs/name/darruma/badger-tokens-arbitrum"
        ),
        f"tokens-{Network.Fantom}": (
            "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens-fantom"
        ),
        "fuse": "https://api.thegraph.com/subgraphs/name/darruma/fuse-subgraph-badger",
        "thegraph": "https://api.thegraph.com/index-node/graphql",
        "nfts": "https://api.thegraph.com/subgraphs/name/darruma/badger-nfts",
        "across": "https://api.thegraph.com/subgraphs/name/darruma/badger-across"
    },
    Environment.Staging: {
    }
}
