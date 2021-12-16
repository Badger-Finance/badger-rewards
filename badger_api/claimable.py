from functools import lru_cache
from typing import Dict

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from helpers.discord import send_error_to_discord
from helpers.enums import Network
from rewards.aws.helpers import dynamodb, get_metadata_table, get_snapshot_table
from subgraph.queries.setts import last_synced_block


def get_latest_claimable_metadata(
    chain: Network
) -> Dict:
    kce = Key('chain').eq(chain) & Key('startBlock').between(0, last_synced_block(chain))
    table = dynamodb.Table(get_metadata_table())
    try:
        output = table.query(KeyConditionExpression=kce, ScanIndexForward=False, Limit=1)
    except ClientError as e:
        send_error_to_discord(
            e,
            f"Database Error \n ```{e.response['Error']['Message']}```",
            "Negative Rewards Error",
            chain
        )
        raise e
    else:
        return output["Item"]

def get_claimable_balances(chain: Network, chain_start_block: str) -> Dict[str, float]:
    table = dynamodb.Table(get_snapshot_table())
    try:
        response = table.get_item(
            Key={
                'chain': chain,
                'chainStartBlock': chain_start_block,
            }
        )
    except ClientError as e:
        send_error_to_discord(
            e,
            f"Database Error \n ```{e.response['Error']['Message']}```",
            "Negative Rewards Error",
            chain
        )
        raise e
    else:
        return response["Item"]["claimableBalances"]


def get_latest_claimable_snapshot(
    chain: Network
):
    metadata = get_latest_claimable_metadata(
        chain,
    )
    return get_claimable_balances(chain, metadata["chainStartBlock"])
