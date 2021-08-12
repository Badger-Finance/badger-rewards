import os


class EnvConfig:
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", '')
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", '')
        self.graph_api_key = os.getenv("GRAPH_API_KEY", '')
        self.test_webhook_url = os.getenv("TEST_WEBHOOK_URL", '')
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL", '')
        self.test = os.getenv("TEST", 'False').lower() in ['true', '1', 't', 'y', 'yes']

    def get_webhook_url(self):
        if(self.test):
            return self.test_webhook_url
        else:
            return self.discord_webhook_url

env_config = EnvConfig()
