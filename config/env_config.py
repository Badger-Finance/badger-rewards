from rewards.aws.helpers import get_secret
import os
from decouple import config
from web3 import Web3
from web3.middleware import geth_poa_middleware


class EnvConfig:
    def __init__(self):

        self.graph_api_key = config("GRAPH_API_KEY")
        self.test_webhook_url = config("TEST_WEBHOOK_URL")
        self.discord_webhook_url = config("DISCORD_WEBHOOK_URL")
        self.test = True
        polygon = Web3(Web3.HTTPProvider(config("POLYGON_NODE_URL")))
        polygon.middleware_onion.inject(geth_poa_middleware, layer=0)

        self.web3 = {
            "eth": Web3(Web3.HTTPProvider(config("ETH_NODE_URL"))),
            "bsc": Web3(Web3.HTTPProvider(config("BSC_NODE_URL"))),
            "polygon": polygon,
        }

    def get_web3(self, chain="eth"):
        return self.web3[chain]

    def get_webhook_url(self):
        if self.test:
            return self.test_webhook_url
        else:
            return self.discord_webhook_url


env_config = EnvConfig()
