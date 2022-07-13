from config.singletons import env_config

urls = {
    "staging": "https://staging-api.badger.com/v2",
    "prod": "https://api.badger.com/v2",
}


def get_api_base_path() -> str:
    if env_config.test or env_config.staging:
        return urls["staging"]
    elif env_config.production:
        return urls["prod"]

    raise EnvironmentError("invalid environment set")


def get_api_specific_path(stage: str) -> str:
    if stage == "staging" or stage == "test":
        return urls["staging"]
    elif stage == "prod":
        return urls["prod"]

    raise EnvironmentError("Invalid environment provided")
