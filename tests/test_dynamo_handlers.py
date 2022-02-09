import os
from unittest.mock import MagicMock

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_dynamodb2
from moto.core import patch_resource
from moto.dynamodb2.models import Table

from helpers.enums import Network
from rewards.aws.helpers import dynamodb
from rewards.dynamo_handlers import put_rewards_data


@pytest.fixture
def dynamodb_rewards_table() -> Table:
    patch_resource(dynamodb)
    with mock_dynamodb2():
        dynamodb_client = boto3.client(
            "dynamodb",
            region_name="us-west-1",
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
        dynamodb_client.create_table(
            TableName="rewards-staging",
            KeySchema=[
                {"AttributeName": "networkCycle", "KeyType": "HASH"},
                {"AttributeName": "cycle", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "networkCycle", "AttributeType": "S"},
                {"AttributeName": "cycle", "AttributeType": "N"},
                {"AttributeName": "endBlock", "AttributeType": "N"},
                {"AttributeName": "network", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "IndexRewardsOnNetworkAndEndBlock",
                    "KeySchema": [
                        {"AttributeName": "network", "KeyType": "HASH"},
                        {"AttributeName": "endBlock", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )
        dynamodb_resource = boto3.resource(
            "dynamodb",
            region_name="us-west-1",
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )

        rewards_table = dynamodb_resource.Table("rewards-staging")
        yield rewards_table


def test_put_rewards_happy(dynamodb_rewards_table):
    cycle = 123
    start_block = 1
    end_block = 100
    network = Network.Ethereum
    rewards_data = {'some': "data"}
    put_rewards_data(Network.Ethereum, cycle, start_block, end_block, rewards_data)
    # noinspection PyArgumentList
    response = dynamodb_rewards_table.get_item(
        Key={
            'networkCycle': f"{network}-{cycle}",
            'cycle': cycle
        }
    )
    item = response['Item']
    assert item['cycle'] == cycle
    assert item['networkCycle'] == f"{network}-{cycle}"
    assert item['startBlock'] == start_block
    assert item['endBlock'] == end_block
    assert item['rewardsData'] == rewards_data


def test_put_rewards_unhappy(dynamodb_rewards_table, mocker):
    """
    Test for situation when dynamo raises err on table.put_item()
    """
    discord = mocker.patch(
        "rewards.dynamo_handlers.send_error_to_discord",
    )
    mocker.patch(
        "rewards.dynamo_handlers.dynamodb.Table",
        return_value=MagicMock(
            put_item=MagicMock(
                side_effect=ClientError({'Error': {'Message': "stuff happened"}}, '')
            )
        )
    )
    put_rewards_data(Network.Ethereum, 1, 123, 123, {})
    assert discord.called
