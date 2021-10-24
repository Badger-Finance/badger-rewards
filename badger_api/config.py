from config.env_config import env_config

urls = {
    "staging": "https://laiv44udi0.execute-api.us-west-1.amazonaws.com/staging/v2",
    "prod": "https://2k2ccquid1.execute-api.us-west-1.amazonaws.com/prod/v2",
}


def get_api_base_path() -> str:
    return urls["staging"] if env_config.test else urls["prod"]
