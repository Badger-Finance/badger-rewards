from rewards.aws.helpers import get_secret
from decouple import config
from web3 import Web3
from web3.middleware import geth_poa_middleware


class EnvConfig:
    def __init__(self):
        self.test = config("TEST", "False").lower() in ["true", "1", "t", "y", "yes"]
        self.graph_api_key = get_secret(
            "boost-bot/graph-api-key-d", "GRAPH_API_KEY", test=self.test
        )
        self.test_webhook_url = get_secret(
            "boost-bot/test-discord-url", "TEST_WEBHOOK_URL", test=self.test
        )
        self.discord_webhook_url = get_secret(
            "boost-bot/prod-discord-url", "DISCORD_WEBHOOK_URL", test=self.test
        )

        self.explorer_api_keys = {
            "eth": get_secret("keepers/etherscan", "ETHERSCAN_TOKEN", test=self.test),
            "polygon": get_secret(
                "keepers/polygonscan", "POLYGONSCAN_TOKEN", test=self.test
            ),
            "arbitrum": get_secret(
                "keepers/arbiscan", "ARBISCAN_TOKEN", test=self.test
            ),
        }
        polygon = self.make_provider("quiknode/poly-node-url", "POLYGON_NODE_URL")
        polygon.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.web3 = {
            "eth": self.make_provider("quiknode/eth-node-url", "NODE_URL"),
            "arbitrum": self.make_provider(
                "alchemy/arbitrum-node-url", "ARBITRUM_NODE_URL"
            ),
            "polygon": polygon,
        }

    def get_web3(self, chain: str = "eth") -> Web3:
        return self.web3[chain]

    def get_explorer_api_key(self, chain: str) -> str:
        return self.explorer_api_keys[chain]

    def make_provider(self, secret_name: str, secret_key: str) -> Web3:
        return Web3(
            Web3.HTTPProvider(get_secret(secret_name, secret_key, test=self.test))
        )

    def get_webhook_url(self) -> str:
        if self.test:
            return self.test_webhook_url
        else:
            return self.discord_webhook_url


env_config = EnvConfig()
