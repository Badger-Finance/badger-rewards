from classes.EnvConfig import env_config

import boto3
from rich.console import Console

console = Console()

s3 = boto3.client(
    "s3",
    aws_access_key_id=env_config.aws_access_key_id,
    aws_secret_access_key=env_config.aws_secret_access_key,
)


def upload_boosts(test):
    fileName = "badger-boosts.json"

    if test:
        bucket = "badger-staging-merkle-proofs"
    else:
        bucket = "badger-merkle-proofs"
    console.log("Uploading file to s3://" + bucket + "/" + fileName)
    s3.upload_file(fileName, bucket, fileName)
    console.log("✅ Uploaded file to s3://" + bucket + "/" + fileName)
