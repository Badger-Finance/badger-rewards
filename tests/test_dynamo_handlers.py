import os

import boto3
import pytest
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
            AttributeDefinitions=[
                {"AttributeName": "network-cycle", "AttributeType": "S"},
                {"AttributeName": "cycle", "AttributeType": "N"},
            ],
            KeySchema=[
                {"AttributeName": "network-cycle", "KeyType": "HASH"},
                {"AttributeName": "cycle", "KeyType": "RANGE"},
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
    end_block = 100
    network = Network.Ethereum
    rewards_data = {'some': "data"}
    put_rewards_data(Network.Ethereum, cycle, end_block, rewards_data)
    # noinspection PyArgumentList
    response = dynamodb_rewards_table.get_item(
        Key={
            'network-cycle': f"{network}-{cycle}",
            'cycle': cycle
        }
    )
    item = response['Item']
    assert item['cycle'] == cycle
    assert item['network-cycle'] == f"{network}-{cycle}"
    assert item['end_block'] == end_block
    assert item['rewards_data'] == rewards_data
