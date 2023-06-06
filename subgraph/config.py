from helpers.enums import (
    Environment,
    Network,
    SubgraphUrlType,
)

subgraph_urls: dict[Environment, dict[str, dict[SubgraphUrlType, str]]] = {
    Environment.Production: {
        # Chain graphs
        Network.BinanceSmartChain: (
            {SubgraphUrlType.Plain:
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-bsc"}
        ),
        Network.Ethereum: ({SubgraphUrlType.AWS: "badger-rewards/badger-vaults-ethereum-gql-url"}),
        Network.Polygon: (
            {SubgraphUrlType.Plain:
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-polygon"}
        ),
        Network.Arbitrum: (
            {SubgraphUrlType.Plain:
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-arbitrum"}
        ),
        Network.Fantom: (
            {SubgraphUrlType.Plain:
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-fantom"}
        ),
        # Token graphs
        f"tokens_{Network.Ethereum}": (
            {SubgraphUrlType.AWS: "badger-rewards/badger-erc20s-ethereum-gql-url"}
        ),
        f"tokens_{Network.BinanceSmartChain}": (
            {SubgraphUrlType.Plain:
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens-bsc"}
        ),
        f"tokens_{Network.Polygon}": (
            {SubgraphUrlType.Plain:
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens-polygon"}
        ),
        f"tokens_{Network.Arbitrum}": (
            {SubgraphUrlType.Plain:
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens-arbitrum"}
        ),
        f"tokens_{Network.Fantom}": (
            {SubgraphUrlType.Plain:
                "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-tokens-fantom"}
        ),
        "fuse": {SubgraphUrlType.AWS: "badger-rewards/badger-fuse-gql-url"},
        "thegraph": {SubgraphUrlType.Plain: "https://api.thegraph.com/index-node/graphql"},
        "nfts": {SubgraphUrlType.AWS: "badger-rewards/badger-nfts-gql-url"},
        "across": {SubgraphUrlType.AWS: "badger-rewards/badger-across-gql-url"}
    },
    Environment.Staging: {
    }
}
