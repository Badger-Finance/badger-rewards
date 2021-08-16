from rewards.aws.helpers import get_secret

import os
from web3 import Web3


class EnvConfig:
    def __init__(self):
        self.graph_api_key = get_secret("boost-bot/graph-api-key-d", "GRAPH_API_KEY")
        self.test_webhook_url = get_secret(
            "boost-bot/test-discord-url", "TEST_WEBHOOK_URL"
        )
        self.test_error_url = get_secret(
            "boost-bot/test-error-discord-url", "TEST_WEBHOOK_URL"
        )
        self.discord_error_url = get_secret(
            "boost-bot/test-error-discord-url", "DISCORD_WEBHOOK_URL"
        )
        self.discord_webhook_url = get_secret(
            "boost-bot/prod-discord-url", "DISCORD_WEBHOOK_URL"
        )
        self.test = os.getenv("TEST", "False").lower() in ["true", "1", "t", "y", "yes"]
        self.web3 = Web3(
            Web3.HTTPProvider(get_secret("quiknode/eth-node-url", "NODE_URL"))
        )

    def get_webhook_url(self, error):
        if self.test:
            if error:
                return self.test_error_url
            return self.test_webhook_url
        else:
            if error:
                return self.discord_error_url
            return self.discord_webhook_url


env_config = EnvConfig()
