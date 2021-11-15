import logging

from decouple import config
from web3 import Web3
from web3.middleware import geth_poa_middleware

from helpers.enums import Environment, Network
from rewards.aws.helpers import get_secret

logging.getLogger("gql.transport.aiohttp").setLevel(logging.WARNING)


class EnvConfig:
    def __init__(self):
        environment = config("ENV", "").lower()
        self.test = environment == Environment.Test
        self.staging = environment == Environment.Staging
        self.production = environment == Environment.Production
        self.kube = config("KUBE", "True").lower() in ["true", "1", "t", "y", "yes"]
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
        }
        # TODO: set polygon back to paid node
        # polygon = self.make_provider("quiknode/poly-node-url", "POLYGON_NODE_URL")
        polygon = Web3(Web3.HTTPProvider("https://polygon-rpc.com/"))
        polygon.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.web3 = {
            Network.Ethereum: self.make_provider("quiknode/eth-node-url", "NODE_URL"),
            Network.Arbitrum: Web3(Web3.HTTPProvider("https://arb1.arbitrum.io/rpc")),
            Network.Polygon: polygon,
        }

        self.is_valid_config()

    def get_web3(self, chain: str = Network.Ethereum) -> Web3:
        return self.web3[chain]

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
