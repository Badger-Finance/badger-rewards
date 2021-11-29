from helpers.enums import Network

subgraph_ids = {}
subgraph_urls = {
    # Chain graphs
    Network.BinanceSmartChain: "https://api.thegraph.com/subgraphs/name/axejintao/badger-dao-bsc",
    Network.Ethereum: "https://api.thegraph.com/subgraphs/name/axejintao/badger-dao",
    Network.Polygon: "https://api.thegraph.com/subgraphs/name/axejintao/badger-dao-polygon",
    Network.Arbitrum: "https://api.thegraph.com/subgraphs/name/axejintao/badger-dao-arbitrum",
    Network.xDai: "https://api.thegraph.com/subgraphs/name/axejintao/badger-dao-xdai",
    # Token graphs
    f"tokens-{Network.Ethereum}": "https://api.thegraph.com/subgraphs/name/darruma/badger-tokens",
    f"tokens-{Network.BinanceSmartChain}": "https://bgraph-bsc.badger.guru/subgraphs/name/swole/badger-subgraph",
    f"tokens-{Network.Polygon}": "https://api.thegraph.com/subgraphs/name/darruma/badger-tokens-polygon",
    f"tokens-{Network.Arbitrum}": "https://api.thegraph.com/subgraphs/name/darruma/badger-tokens-arbitrum",
    # Harvest graphs
    f"harvests-{Network.Ethereum}": "https://api.thegraph.com/subgraphs/name/darruma/badger-harvests",
    f"harvests-{Network.Polygon}": "https://api.thegraph.com/subgraphs/name/darruma/badger-tree-rewards-polygon",
    f"harvests-{Network.Arbitrum}": "https://api.thegraph.com/subgraphs/name/darruma/badger-tree-rewards-arbitrum",
    "fuse": "https://api.thegraph.com/subgraphs/name/darruma/fuse-subgraph-badger",
    "thegraph": "https://api.thegraph.com/index-node/graphql",
    "nfts": "https://api.thegraph.com/subgraphs/name/darruma/badger-nfts"
}
