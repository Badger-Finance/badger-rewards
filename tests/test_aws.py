from unittest.mock import MagicMock

import pytest

from helpers.enums import Network
from rewards.aws.trees import download_latest_tree
from rewards.aws.trees import download_tree
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
