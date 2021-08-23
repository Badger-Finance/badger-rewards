from rewards.aws.helpers import get_secret
import os
from decouple import config
from web3 import Web3
from web3.middleware import geth_poa_middleware


class EnvConfig:
    def __init__(self):
<<<<<<< HEAD
        self.graph_api_key = get_secret("boost-bot/graph-api-key-d", "GRAPH_API_KEY")
        self.test_webhook_url = get_secret(
            "boost-bot/test-discord-url", "TEST_WEBHOOK_URL"
        )
        self.discord_webhook_url = get_secret("DISCORD_WEBHOOK_URL", "")
        self.test = os.getenv("TEST", "False").lower() in ["true", "1", "t", "y", "yes"]
        self.bucket = (
            "badger-staging-merkle-proofs" if self.test else "badger-merkle-proofs"
        )
=======

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
>>>>>>> emissions-calculation

    def get_webhook_url(self):
        if self.test:
            return self.test_webhook_url
        else:
            return self.discord_webhook_url


env_config = EnvConfig()
