import boto3
from rich.console import Console
import json

console = Console()

s3 = boto3.client("s3")
analyticsBucket = "badger-analytics"


def upload_analytics(cycle: int, data):
    """
    Upload analytics data to analytics bucket
    :param cycle: which cycle to upload
    :param data: cycle information
    """
    jsonKey = "logs/{}.json".format(cycle)
    console.log("Uploading file to s3://" + analyticsBucket + "/" + jsonKey)
    s3.put_object(Body=str(json.dumps(data)), Bucket=analyticsBucket, Key=jsonKey, ACL="bucket-owner-full-control")
    console.log("✅ Uploaded file to s3://" + analyticsBucket + "/" + jsonKey)


def upload_schedules(data):
    """
    Upload schedules to analytics bucket
    :param data: schedules to upload
    """
    jsonKey = "schedules.json"
    console.log("Uploading file to s3://" + analyticsBucket + "/" + jsonKey)
    s3.put_object(Body=str(json.dumps(data)), Bucket=analyticsBucket, Key=jsonKey, ACL="bucket-owner-full-control")
    console.log("✅ Uploaded file to s3://" + analyticsBucket + "/" + jsonKey)
