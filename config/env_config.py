import logging

from decouple import config
from web3 import Web3
from web3.middleware import geth_poa_middleware

from helpers.enums import (
    Environment,
    Network,
)
from rewards.aws.helpers import get_secret

logging.getLogger("gql.transport.aiohttp").setLevel(logging.WARNING)

logging.getLogger("gql.transport.aiohttp").setLevel("WARNING")


class NoHealthyNode(Exception):
    pass


class EnvConfig:
    rpc_logger = logging.getLogger("rpc-logger")

    def __init__(self):
        environment = config("ENV", "").lower()
        self.test = environment == Environment.Test
        self.staging = environment == Environment.Staging
        self.production = environment == Environment.Production
        self.kube = config("KUBE", "True").lower() in ["true", "1", "t", "y", "yes"]
        self.fix_cycle = config("FIX_CYCLE", "False").lower() in ["true", "1", "t", "y", "yes"]
        self.graph_api_key = get_secret(
            "boost-bot/graph-api-key-d", "GRAPH_API_KEY", kube=self.kube
        )
        self.test_webhook_url = get_secret(
            "boost-bot/test-discord-url", "TEST_WEBHOOK_URL", kube=self.kube
        )
        self.discord_webhook_url = get_secret(
            "boost-bot/prod-discord-url", "DISCORD_WEBHOOK_URL", kube=self.kube
        )

        self.explorer_api_keys = {
            Network.Ethereum: get_secret(
                "keepers/etherscan", "ETHERSCAN_TOKEN", kube=self.kube
            ),
            Network.Polygon: get_secret(
                "keepers/polygonscan", "POLYGONSCAN_TOKEN", kube=self.kube
            ),
            Network.Arbitrum: get_secret(
                "keepers/arbiscan", "ARBISCAN_TOKEN", kube=self.kube
            ),
            Network.Fantom: get_secret(
                "keepers/ftmscan", "FTMSCAN_TOKEN", kube=self.kube
            )
        }

        polygon = [
            self.make_provider("pokt/poly-node-url", "POLY_NODE_URL"),
            Web3(Web3.HTTPProvider("https://polygon-rpc.com/")),
            self.make_provider("quiknode/poly-node-url", "POLY_NODE_URL"),
            self.make_provider("alchemy/poly-node-url", "POLY_NODE_URL"),
        ]
        for node in polygon:
            node.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.web3 = {
            Network.Ethereum: [
                self.make_provider("pokt/eth-node-url", "NODE_URL"),
                self.make_provider("quiknode/eth-node-url", "NODE_URL"),
                self.make_provider("alchemy/eth-node-url", "NODE_URL"),
                Web3(Web3.HTTPProvider("https://main-rpc.linkpool.io/")),
                Web3(Web3.HTTPProvider("https://rpc.flashbots.net/")),
            ],
            Network.Arbitrum: [
                Web3(Web3.HTTPProvider("https://arb1.arbitrum.io/rpc")),
                self.make_provider("moralis/arbitrum-node-url", "ARBITRUM_NODE_URL"),
                self.make_provider("alchemy/arbitrum-node-url", "ARBITRUM_NODE_URL"),
            ],
            Network.Polygon: polygon,
            Network.Fantom: [
                Web3(Web3.HTTPProvider("https://rpc.ftm.tools/")),
                Web3(Web3.HTTPProvider("https://rpcapi.fantom.network")),
                Web3(Web3.HTTPProvider("https://ftmrpc.ultimatenodes.io")),
                Web3(Web3.HTTPProvider("https://rpc.ankr.com/fantom")),
            ]
        }
        self.is_valid_config()

    def get_web3(self, chain: str = Network.Ethereum) -> Web3:
        return self.get_healthy_node(chain)

    def get_healthy_node(self, chain: Network) -> Web3:
        for node in self.web3[chain]:
            try:
                node.eth.get_block_number()
                return node
            except Exception as e:
                self.rpc_logger.info(f"{node.provider.endpoint_uri} unhealthy")
                self.rpc_logger.info(e)

        raise NoHealthyNode(f"No healthy nodes for chain: {chain}")

    def get_explorer_api_key(self, chain: str) -> str:
        return self.explorer_api_keys[chain]

    def make_provider(self, secret_name: str, secret_key: str) -> Web3:
        return Web3(
            Web3.HTTPProvider(get_secret(secret_name, secret_key, kube=self.kube))
        )

    def get_webhook_url(self) -> str:
        if self.test:
            return self.test_webhook_url
        else:
            return self.discord_webhook_url

    def get_environment(self) -> Environment:
        if self.test:
            return Environment.Test
        elif self.staging:
            return Environment.Staging
        elif self.production:
            return Environment.Production

    def is_valid_config(self):
        assert self.test or self.staging or self.production, "Valid environment not set"
        return True
