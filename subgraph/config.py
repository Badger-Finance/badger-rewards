from helpers.enums import (
    Environment,
    Network,
)

subgraph_urls: dict[Environment, dict[str, dict[str, str]]] = {
    Environment.Production: {
        # Chain graphs
        Network.BinanceSmartChain: (
            {"raw": "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-bsc"}
        ),
        Network.Ethereum: ({"secret": "badger-rewards/badger-vaults-ethereum-gql-url"}),
        Network.Polygon: (
            {"raw":
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-polygon"}
        ),
        Network.Arbitrum: (
            {"raw":
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-arbitrum"}
        ),
        Network.Fantom: (
            {"raw":
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-fantom"}
        ),
        # Token graphs
        f"tokens-{Network.Ethereum}": (
            {"secret": "badger-rewards/badger-erc20s-ethereum-gql-url"}
        ),
        f"tokens-{Network.BinanceSmartChain}": (
            {"raw": "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens-bsc"}
        ),
        f"tokens-{Network.Polygon}": (
            {"raw":
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens-polygon"}
        ),
        f"tokens-{Network.Arbitrum}": (
            {"raw":
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens-arbitrum"}
        ),
        f"tokens-{Network.Fantom}": (
            {"raw":
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens-fantom"}
        ),
        "fuse": {"secret": "badger-rewards/badger-fuse-gql-url"},
        "thegraph": {"raw": "https://api.thegraph.com/index-node/graphql"},
        "nfts": {"secret": "badger-rewards/badger-nfts-gql-url"},
        "across": {"secret": "badger-rewards/badger-across-gql-url"}
    },
    Environment.Staging: {
    }
}
