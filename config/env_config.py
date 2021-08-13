from rewards.aws.helpers import get_secret

import os
from web3 import Web3


class EnvConfig:
    def __init__(self):
        self.graph_api_key = get_secret("boost-bot/graph-api-key-d", "GRAPH_API_KEY")
        self.test_webhook_url = get_secret("boost-bot/test-discord-url", "TEST_WEBHOOK_URL")
        # TODO: use get_secret when we go to prod
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "") # get_secret("DISCORD_WEBHOOK_URL", '')
        self.test = os.getenv("TEST", "False").lower() in ['true', '1', 't', 'y', 'yes']
        self.web3 = Web3(Web3.HTTPProvider(get_secret("quiknode/eth-node-url", "NODE_URL")))

    def get_webhook_url(self):
        if(self.test):
            return self.test_webhook_url
        else:
            return self.discord_webhook_url

env_config = EnvConfig()
