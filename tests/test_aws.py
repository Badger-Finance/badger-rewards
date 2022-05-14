from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from helpers.enums import Network
from rewards.aws.trees import download_latest_tree
from rewards.aws.trees import download_tree
from rewards.aws.trees import upload_tree
from tests.utils import chains


def test_download_latest_tree(mocker):
    """
    Unit test for aws download_latest_tree function
    """
    mocker.patch(
        "rewards.aws.trees.s3.get_object",
        return_value={
            'Body': MagicMock(read=MagicMock(
                return_value=(MagicMock(
                    decode=MagicMock(
                        return_value='{"latest": "tree"}'
                    )
                ))
            ))
        }
    )
    assert download_latest_tree(Network.Ethereum) == {"latest": "tree"}


@pytest.mark.parametrize("chain", chains)
def test_download_tree(mocker, chain):
    """
    Test for func that downloads specific tree
    """
    mocker.patch(
        "rewards.aws.trees.s3.get_object",
        return_value={
            'Body': MagicMock(read=MagicMock(
                return_value=(MagicMock(
                    decode=MagicMock(
                        return_value='{"some": "tree"}'
                    )
                ))
            ))
        }
    )
    assert download_tree("merkle.json", chain) == '{"some": "tree"}'


@pytest.mark.parametrize("chain", chains)
def test_upload_tree(mocker, chain):
    """
    Unit test for tree upload. Checking that all needed s3 methods are called
    """
    put_obj = mocker.patch(
        "rewards.aws.trees.s3.put_object",
    )
    upload_tree("tree.json", {"some": "stuff"}, chain)
    assert put_obj.called


@pytest.mark.parametrize("chain", chains)
def test_upload_tree_unhappy(mocker, chain):
    """
    Unit test for tree upload. Checking that all needed s3 methods are called
    """
    mocker.patch("builtins.open")
    mocker.patch(
        "rewards.aws.trees.s3.put_object",
        side_effect=ClientError({'Error': {'Message': "stuff happened"}}, '')
    )
    console_and_discord = mocker.patch(
        "rewards.aws.trees.console_and_discord",
    )
    with pytest.raises(ClientError):
        upload_tree("tree.json", {"some": "stuff"}, chain)
    assert console_and_discord.called
