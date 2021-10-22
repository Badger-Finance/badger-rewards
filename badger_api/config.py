from config.env_config import env_config
urls = {
    "staging": "https://laiv44udi0.execute-api.us-west-1.amazonaws.com/staging/v2",
    "production": "https://api.badger.finance/v2",
}

def get_api_url() -> str:
    return urls["staging"] if env_config.test else urls["production"]