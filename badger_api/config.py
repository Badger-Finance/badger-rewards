from config.env_config import env_config

urls = {
    "staging": "https://staging-api.badger.com/v2",
    "prod": "https://api.badger.com/v2",
}


def get_api_base_path() -> str:
    return urls["prod"]
    return urls["staging"] if env_config.test else urls["prod"]
