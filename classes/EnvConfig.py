from helpers.constants import debug

import os

class EnvConfig:
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.graph_api_key = os.getenv("GRAPH_API_KEY")
        self.debug = debug


env_config = EnvConfig()