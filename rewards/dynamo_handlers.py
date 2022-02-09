from typing import Dict

from botocore.exceptions import ClientError

from helpers.discord import send_error_to_discord
from helpers.enums import Network
from rewards.aws.helpers import dynamodb
from rewards.aws.helpers import get_rewards_table


def put_rewards_data(
        chain: Network, cycle: int, end_block: int,
        rewards_data: Dict
) -> None:
    """
    Helper function to store rewards data to Dynamodb table.
    Note that `rewards_data` should be JSON serializable
    """
    table = dynamodb.Table(get_rewards_table())
    try:
        table.put_item(
            Item={
                'network-cycle': f"{chain}-{cycle}",
                'network': chain,
                'cycle': cycle,
                'end_block': end_block,
                'rewards_data': rewards_data,
            }
        )
    except ClientError as e:
        send_error_to_discord(
            e,
            f"Database Error \n ```{e.response['Error']['Message']}```",
            "Client Error",
            chain,
        )
