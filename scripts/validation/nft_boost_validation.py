import json
import os

import boto3
from dotenv import load_dotenv

from helpers.constants import CHAIN_IDS, S3_BUCKETS
from helpers.enums import BucketType, Environment, Network

load_dotenv()


def download_boosts(chain: str, bucket: str):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    )

    print(f"DOWNLOADING BOOST FOR {chain.upper()} FROM {bucket}")
    chain_id = CHAIN_IDS[chain]

    boost_file_name = f"badger-boosts-{chain_id}.json"
    s3ClientObj = s3.get_object(Bucket=bucket, Key=boost_file_name)
    data = json.loads(s3ClientObj["Body"].read().decode("utf-8"))
    return data


chain = Network.Ethereum

prod_boosts = download_boosts(
    chain, S3_BUCKETS[BucketType.Merkle][Environment.Production]
)
stag_boosts = download_boosts(
    chain, S3_BUCKETS[BucketType.Merkle][Environment.Staging]
)

PROD_USER_LIST = prod_boosts["userData"].keys()
differences = {}

for addr in PROD_USER_LIST:
    
    prod_native = float(prod_boosts["userData"][addr]["nativeBalance"])
    stag_native = float(stag_boosts["userData"][addr]["nativeBalance"])



    if prod_native + 150 <= stag_native:
        differences[addr] = {
            'prod': prod_native,
            'stag': stag_native,
            'diff': float(stag_native) - float(prod_native)
        }
        with open('boost-differences.json', "w") as fp:
            json.dump(differences, fp, indent=4)

