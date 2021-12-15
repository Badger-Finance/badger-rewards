from typing import Dict

from boto3.dynamodb.conditions import Attr, Key

from helpers.enums import Network
from rewards.aws.helpers import dynamodb


def get_latest_claimable_metadata(
    chain: Network, start_block: int, end_block: int
) -> Dict:
    pass

def get_claimable_balances(chain: Network, id: str) -> Dict[str, float]:
    pass

def get_latest_claimable_snapshot(
    chain: Network, start_block: int, end_block: int
):
    metadata = get_latest_claimable_metadata(
        chain,
        start_block,
        end_block
    )
    return get_claimable_balances(chain, metadata["id"])

