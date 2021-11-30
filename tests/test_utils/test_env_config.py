import logging
import os

import pytest

os.environ["KUBE"] = "False"
os.environ["AWS_ACCESS_KEY_ID"] = ""
os.environ["AWS_SECRET_ACCESS_KEY"] = ""

from config.env_config import EnvConfig
from helpers.enums import Environment

logger = logging.getLogger("test-env-config")


def test_valid_environment():
    if "ENV" in os.environ:
        os.environ.pop("ENV")
    with pytest.raises(AssertionError):
        EnvConfig()

    os.environ["ENV"] = "test"
    env_config = EnvConfig()
    assert env_config.is_valid_config()


def test_get_environment():
    enum = [Environment.Test, Environment.Staging, Environment.Production]
    vals = ["test", "stg", "prod"]
    for expected, val in zip(enum, vals):
        if "ENV" in os.environ:
            os.environ.pop("ENV")
        os.environ["ENV"] = val
        env_config = EnvConfig()
        assert env_config.get_environment() == expected
