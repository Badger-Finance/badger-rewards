from unittest.mock import MagicMock

from helpers.enums import Network
from rewards.aws.trees import download_latest_tree


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
