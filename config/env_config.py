from rewards.aws.helpers import get_secret
from decouple import config
from web3 import Web3
from web3.middleware import geth_poa_middleware
from helpers.enums import Network


class EnvConfig:
    def __init__(self):
        self.test = config("TEST", "False").lower() in ["true", "1", "t", "y", "yes"]
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
        polygon = self.make_provider("quiknode/poly-node-url", "POLYGON_NODE_URL")
        polygon.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.web3 = {
            Network.Ethereum: self.make_provider("quiknode/eth-node-url", "NODE_URL"),
            Network.Arbitrum: self.make_provider(
                "alchemy/arbitrum-node-url", "ARBITRUM_NODE_URL"
            ),
            Network.Polygon: polygon,
        }

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


env_config = EnvConfig()
