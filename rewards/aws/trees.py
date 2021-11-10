from config.singletons import env_config
from rich.console import Console
from rewards.aws.helpers import get_bucket, s3
import json
from typing import Dict
from rewards.aws.helpers import s3
from helpers.enums import Network

console = Console()


def download_latest_tree(chain: str):
    """
    Download the latest merkle tree that was uploaded for a chain
    :param chain: the chain from which to fetch the latest tree from
    """
    if chain == Network.Ethereum:
        key = "badger-tree.json"
    else:
        key = f"badger-tree-{chain}.json"

    target = {
        "bucket": get_bucket(env_config.production),
        "key": key,
    }  # badger-api production

    console.print("Downloading latest rewards file from s3: " + target["bucket"])
    s3_clientobj = s3.get_object(Bucket=target["bucket"], Key=target["key"])
    s3_clientdata = s3_clientobj["Body"].read().decode("utf-8")
    return json.loads(s3_clientdata)


def download_tree(file_name: str, chain: str):
    """
    Download a specific tree based on the merkle root of that tree
    :param file_name: fileName of tree to download
    """
    if chain == Network.Ethereum:
        tree_bucket = "badger-json"
    else:
        tree_bucket = f"badger-json-{chain}"

    tree_file_key = "rewards/" + file_name

    console.print("Downloading file from s3: " + tree_file_key)

    s3_clientobj = s3.get_object(Bucket=tree_bucket, Key=tree_file_key)
    s3_clientdata = s3_clientobj["Body"].read().decode("utf-8")

    return s3_clientdata


def download_past_trees(test: bool, number: int):
    """
    Download a number of past trees
    :param number: number of trees to download from the latest
    """
    trees = []
    key = "badger-tree.json"
    bucket = env_config.bucket
    response = s3.list_object_versions(Prefix=key, Bucket=bucket)
    versions = response["Versions"][:number]
    for version in versions:
        console.log(version["Key"], version["VersionId"])
        # yield version
        s3_client_obj = s3.get_object(
            Bucket=bucket, Key=version["Key"], VersionId=version["VersionId"]
        )
        trees.append(s3_client_obj["Body"].read())
    return trees


def upload_tree(
    file_name: str,
    data: Dict,
    chain: str,
    bucket: str = "badger-json",
    staging: bool = False,
):
    """
    Upload the badger tree to multiple buckets
    :param fileName: the filename of the uploaded bucket
    :param data: the data to push
    """
    chain_id = env_config.get_web3(chain).eth.chain_id

    if chain == Network.Ethereum:
        key = "badger-tree.json"
        rewards_bucket = "badger-json"
    else:
        key = f"badger-tree-{chain_id}.json"
        rewards_bucket = f"badger-json-{chain}"

    upload_targets = [
        {
            "bucket": "badger-staging-merkle-proofs",
            "key": key,
        }  # badger-api staging no matter what
    ]

    if not staging:
        upload_targets.append(
            {
                "bucket": rewards_bucket,
                "key": "rewards/" + file_name,
            },  # badger-json rewards api
        )

        upload_targets.append(
            {
                "bucket": "badger-merkle-proofs",
                "key": key,
            }  # badger-api production
        )

    for target in upload_targets:
        console.print(
            "Uploading file to s3://" + target["bucket"] + "/" + target["key"]
        )
        s3.put_object(
            Body=str(json.dumps(data)),
            Bucket=target["bucket"],
            Key=target["key"],
            ACL="bucket-owner-full-control",
        )
        console.print(
            "✅ Uploaded file to s3://" + target["bucket"] + "/" + target["key"]
        )
