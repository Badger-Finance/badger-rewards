import json

from rich.console import Console

from rewards.aws.helpers import s3

console = Console()
analytics_bucket = "badger-analytics"


def upload_analytics(chain: str, cycle: int, data):
    """
    Upload analytics data to analytics bucket
    :param cycle: which cycle to upload
    :param data: cycle information
    """
    json_key = f"logs/{chain}/{cycle}.json"
    console.log("Uploading file to s3://" + analytics_bucket + "/" + json_key)
    s3.put_object(
        Body=str(json.dumps(data)),
        Bucket=analytics_bucket,
        Key=json_key,
        ACL="bucket-owner-full-control",
    )
    console.log("✅ Uploaded file to s3://" + analytics_bucket + "/" + json_key)


def upload_schedules(chain: str, data):
    """
    Upload schedules to analytics bucket
    :param data: schedules to upload
    """
    json_key = f"schedules-{chain}.json"
    console.log("Uploading file to s3://" + analytics_bucket + "/" + json_key)
    s3.put_object(
        Body=str(json.dumps(data)),
        Bucket=analytics_bucket,
        Key=json_key,
        ACL="bucket-owner-full-control",
    )
    console.log("✅ Uploaded file to s3://" + analytics_bucket + "/" + json_key)
