from typing import Dict

from botocore.exceptions import ClientError

from helpers.discord import send_error_to_discord
from helpers.enums import Network
from rewards.aws.helpers import dynamodb
from rewards.aws.helpers import get_rewards_table
from config.singletons import env_config


def put_rewards_data(
        chain: Network, cycle: int, start_block: int, end_block: int,
        rewards_data: Dict
) -> None:
    """
    Helper function to store rewards data to Dynamodb table.
    Note that `rewards_data` should be JSON serializable
    """
    table = dynamodb.Table(get_rewards_table(env_config.production))
    try:
        table.put_item(
            Item={
                'networkCycle': f"{chain}-{cycle}",
                'cycle': cycle,
                'network': chain,
                'startBlock': start_block,
                'endBlock': end_block,
                'rewardsData': rewards_data,
            }
        )
    except ClientError as e:
        # Gracefully quit function without raising exception
        send_error_to_discord(
            e,
            f"Database Error \n ```{e.response['Error']['Message']}```",
            "Client Error",
            chain,
        )
