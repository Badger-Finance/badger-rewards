from helpers.enums import (
    Environment,
    Network,
)
from config.singletons import env_config

subgraph_urls = {
    Environment.Production: {
        # Chain graphs
        Network.BinanceSmartChain: (
            "https://api.thegraph.com/subgraphs/name/badger-finance/badger-dao-setts-bsc"
        ),
        Network.Ethereum: (env_config.get_graph_api_key(
            "badger-rewards/badger-vaults-ethereum-gql-url", "SUBGRAPH_URL"),
        ),
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
            env_config.get_graph_api_key(
                "badger-rewards/badger-erc20s-ethereum-gql-url", "SUBGRAPH_URL"),
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
        "fuse": env_config.get_graph_api_key(
            "badger-rewards/badger-fuse-gql-url", "SUBGRAPH_URL"),
        "thegraph": "https://api.thegraph.com/index-node/graphql",
        "nfts": env_config.get_graph_api_key(
            "badger-rewards/badger-nfts-gql-url", "SUBGRAPH_URL"),
        "across": env_config.get_graph_api_key(
            "badger-rewards/badger-across-gql-url", "SUBGRAPH_URL")
    },
    Environment.Staging: {
    }
}
