from rewards.aws.helpers import get_secret
import os
from decouple import config
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account


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
        polygon = self.make_provider("quiknode/poly-node-url", "POLYGON_NODE_URL")
        polygon.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.web3 = {
            "eth": self.make_provider("quiknode/eth-node-url", "NODE_URL"),
            "bsc": self.make_provider("quiknode/bsc-node-url", "BSC_NODE_URL"),
            "polygon": polygon,
        }

    def make_provider(self,name, key):
        return Web3(Web3.HTTPProvider(
            endpoint_uri=get_secret(name,key, test=self.test),
            request_kwargs={'timeout': 30}
        ))
        
    def get_web3(self, chain="eth"):
        return self.web3[chain]

    def get_webhook_url(self) -> str:
        if self.test:
            return self.test_webhook_url
        else:
            return self.discord_webhook_url


env_config = EnvConfig()
