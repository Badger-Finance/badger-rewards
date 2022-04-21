import os

import boto3
import pytest
from moto import mock_dynamodb2
from decimal import Decimal
from badger_api.requests import (
    fetch_token_names,
    fetch_token_prices,
)
from subgraph.queries.tokens import fetch_token_balances
from rewards.classes.Snapshot import Snapshot
from rewards.snapshot.claims_snapshot import claims_snapshot
from config.constants import addresses

TOKEN_SNAPSHOT_DATA = (
    {
        "0x01fb5de8847e570899d3e00029Ae9cD9cB40E5d7": Decimal(44557.11578),
        "0x1f3e2aB8FE0C6E1f47acDcaa0b3B9db4044f7909": Decimal(354.388194),
    },
    {
        "0x017b3763b8a034F8655D46345e3EB42555E39064": Decimal(0.000091143809567686612959),
        "0x01ebce016681D076667BDb823EBE1f76830DA6Fa": Decimal(0.000055073869881086331795)
    },
)

CHAIN_SETT_SNAPSHOT_DATA = (
    {
        "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 2.0106850985422638,
        "0x0000001d2B0A08A235276e8765aa1A659Aae58bb": 44.602734829161123,
    },
    {
        "0x000E8C608473DCeE93021EB1d39fb4A7D7E7d780": 153519.6403430607008,
        "0x00369B46cd0c232Ff5dc1d376248c4954CE645Ee": 2102.2812933779145123,
        "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 1.0106850985422638,
        "0x0000001d2B0A08A235276e8765aa1A659Aae58bb": 12.602734829161123,
    },
)

NFT_SNAPSHOT_DATA = {
    "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 3446.0,
    "0x0000001d2B0A08A235276e8765aa1A659Aae58bb": 3536.0,
}

CHAIN_CLAIMS_SNAPSHOT_DATA = (
    {
        "0x0000000000007F150Bd6f54c40A34d7C3d5e9f56": 44557.11578,
        "0x0000001d2B0A08A235276e8765aa1A659Aae58bb": 4354.388194,
    },
    {
        "0x000E8C608473DCeE93021EB1d39fb4A7D7E7d780": 0.000091143809567686612959,
        "0x00369B46cd0c232Ff5dc1d376248c4954CE645Ee": 0.000055073869881086331795,
    },
)


@pytest.fixture
def mock_discord(mocker):
    return mocker.patch("helpers.http_session.send_message_to_discord")


@pytest.fixture
def mock_snapshots(mocker):
    mocker.patch(
        "rewards.boost.boost_utils.token_snapshot_usd", return_value=TOKEN_SNAPSHOT_DATA
    )
    mocker.patch(
        "rewards.boost.boost_utils.chain_snapshot_usd",
        return_value=CHAIN_SETT_SNAPSHOT_DATA,
    )
    mocker.patch(
        "rewards.boost.boost_utils.claims_snapshot_usd",
        return_value=CHAIN_CLAIMS_SNAPSHOT_DATA,
    )

    mocker.patch(
        "rewards.boost.boost_utils.nft_snapshot_usd", return_value=NFT_SNAPSHOT_DATA
    )
    mocker.patch(
        "rewards.boost.boost_utils.fuse_snapshot_of_token",
        return_value=Snapshot(addresses.BVECVX, {
            "0x01fb5de8847e570899d3e00029Ae9cD9cB40E5d7": Decimal(100),
            "0x017b3763b8a034F8655D46345e3EB42555E39064": Decimal(50),
        })
    )


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-west-1"


@pytest.fixture
def setup_dynamodb():
    with mock_dynamodb2():
        dynamodb_client = boto3.client(
            "dynamodb",
            region_name="us-west-1",
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )
        dynamodb_client.create_table(
            TableName="metadata-staging",
            AttributeDefinitions=[
                {"AttributeName": "chainStartBlock", "AttributeType": "S"},
                {"AttributeName": "chain", "AttributeType": "S"},
                {"AttributeName": "startBlock", "AttributeType": "N"},
            ],
            KeySchema=[{"AttributeName": "chainStartBlock", "KeyType": "HASH"}],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "IndexMetadataChainAndStartBlock",
                    "KeySchema": [
                        {"AttributeName": "chain", "KeyType": "HASH"},
                        {"AttributeName": "startBlock", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
        )

        dynamodb_client.create_table(
            TableName="unclaimed-snapshots-staging",
            AttributeDefinitions=[
                {"AttributeName": "chainStartBlock", "AttributeType": "S"},
                {"AttributeName": "address", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "chainStartBlock", "KeyType": "HASH"},
                {"AttributeName": "address", "KeyType": "RANGE"},
            ],
        )

        dynamodb_resource = boto3.resource(
            "dynamodb",
            region_name="us-west-1",
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        )

        metadata_table = dynamodb_resource.Table("metadata-staging")
        metadata_table.update_item(
            Key={"chainStartBlock": "ethereum_13957559"},
            ExpressionAttributeNames={
                "#CH": "chain",
                "#EB": "endBlock",
                "#SB": "startBlock",
            },
            ExpressionAttributeValues={
                ":ch": "ethereum",
                ":eb": 14576829,
                ":sb": 13957559,
            },
            UpdateExpression="SET #CH=:ch, #EB=:eb, #SB=:sb",
        )
        metadata_table.update_item(
            Key={"chainStartBlock": "polygon_22597558"},
            ExpressionAttributeNames={
                "#CH": "chain",
                "#EB": "endBlock",
                "#SB": "startBlock",
            },
            ExpressionAttributeValues={
                ":ch": "polygon",
                ":eb": 23599058,
                ":sb": 22597558,
            },
            UpdateExpression="SET #CH=:ch, #EB=:eb, #SB=:sb",
        )
        metadata_table.update_item(
            Key={"chainStartBlock": "arbitrum_3902125"},
            ExpressionAttributeNames={
                "#CH": "chain",
                "#EB": "endBlock",
                "#SB": "startBlock",
            },
            ExpressionAttributeValues={
                ":ch": "arbitrum",
                ":eb": 14576829,
                ":sb": 3902125,
            },
            UpdateExpression="SET #CH=:ch, #EB=:eb, #SB=:sb",
        )

        unclaimed_snapshots_table = dynamodb_resource.Table(
            "unclaimed-snapshots-staging"
        )
        unclaimed_snapshots_table.update_item(
            Key={
                "chainStartBlock": "ethereum_13957559",
                "address": "0x00C67d9D6D3D13b42a87424E145826c467CcCd84",
            },
            ExpressionAttributeNames={
                "#A": "address",
                "#C": "chain",
                "#CB": "claimableBalances",
            },
            ExpressionAttributeValues={
                ":a": "0x00C67d9D6D3D13b42a87424E145826c467CcCd84",
                ":c": "ethereum",
                ":cb": [],
            },
            UpdateExpression="SET #A=:a, #C=:c, #CB=:cb",
        )
        unclaimed_snapshots_table.update_item(
            Key={
                "chainStartBlock": "polygon_22597558",
                "address": "0x00C67d9D6D3D13b42a87424E145826c467CcCd84",
            },
            ExpressionAttributeNames={
                "#A": "address",
                "#C": "chain",
                "#CB": "claimableBalances",
            },
            ExpressionAttributeValues={
                ":a": "0x00C67d9D6D3D13b42a87424E145826c467CcCd84",
                ":c": "polygon",
                ":cb": [],
            },
            UpdateExpression="SET #A=:a, #C=:c, #CB=:cb",
        )
        unclaimed_snapshots_table.update_item(
            Key={
                "chainStartBlock": "arbitrum_3902125",
                "address": "0x00C67d9D6D3D13b42a87424E145826c467CcCd84",
            },
            ExpressionAttributeNames={
                "#A": "address",
                "#C": "chain",
                "#CB": "claimableBalances",
            },
            ExpressionAttributeValues={
                ":a": "0x00C67d9D6D3D13b42a87424E145826c467CcCd84",
                ":c": "arbitrum",
                ":cb": [],
            },
            UpdateExpression="SET #A=:a, #C=:c, #CB=:cb",
        )

        yield dynamodb_client, dynamodb_resource


@pytest.fixture(autouse=True)
def clear_cache():
    fetch_token_names.cache_clear()
    fetch_token_prices.cache_clear()
    claims_snapshot.cache_clear()
    fetch_token_balances.cache_clear()


@pytest.fixture
def fetch_token_mock(mocker):
    value = {
        'decimals': 18,
        'name': "BADGER",
    }
    mocker.patch(
        "rewards.utils.token_utils.fetch_token",
        return_value=value
    )
    mocker.patch(
        "rewards.snapshot.chain_snapshot.fetch_token",
        return_value=value
    )
    mocker.patch(
        "badger_api.requests.fetch_token",
        return_value=value
    )
