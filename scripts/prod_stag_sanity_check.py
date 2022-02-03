import json
import os
import random
from math import isclose

import boto3
from dotenv import load_dotenv

from config.constants.aws import S3_BUCKETS
from config.constants.chain_mappings import CHAIN_IDS
from config.constants.emissions import BOOST_CHAINS
from helpers.enums import BucketType, Environment

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


for chain in BOOST_CHAINS:
    prod_boosts = download_boosts(
        chain, S3_BUCKETS[BucketType.Merkle][Environment.Production]
    )
    stag_boosts = download_boosts(
        chain, S3_BUCKETS[BucketType.Merkle][Environment.Staging]
    )

    print(len(prod_boosts["userData"].keys()))
    print(len(stag_boosts["userData"].keys()))
    for addr in prod_boosts["userData"].keys():
        if addr not in stag_boosts["userData"].keys():
            print(addr)

    assert len(prod_boosts["userData"].keys()) == len(stag_boosts["userData"].keys())

    sample = random.sample(prod_boosts["userData"].keys(), 20)

    for addr in sample:
        prod_boost = prod_boosts["userData"][addr]["boost"]
        prod_native = prod_boosts["userData"][addr]["nativeBalance"]
        prod_non_native = prod_boosts["userData"][addr]["nonNativeBalance"]
        prod_stake_ratio = prod_boosts["userData"][addr]["stakeRatio"]

        stag_boost = stag_boosts["userData"][addr]["boost"]
        stag_native = stag_boosts["userData"][addr]["nativeBalance"]
        stag_non_native = stag_boosts["userData"][addr]["nonNativeBalance"]
        stag_stake_ratio = stag_boosts["userData"][addr]["stakeRatio"]

        boost_is_eq = isclose(prod_boost, stag_boost, abs_tol=1e-2)
        native_is_eq = isclose(prod_native, stag_native, abs_tol=1e-2)
        non_native_is_eq = isclose(prod_non_native, stag_non_native, abs_tol=1e-2)
        stake_is_eq = isclose(prod_stake_ratio, stag_stake_ratio, abs_tol=1e-2)

        print(f"Address {addr}:")
        print(f"Boost is approximately equal: {boost_is_eq}")
        if not boost_is_eq:
            print(f"{prod_boost} != {stag_boost}")
        print(f"Native Balance is approximately equal: {native_is_eq}")
        if not native_is_eq:
            print(f"{prod_native} != {stag_native}")
        print(f"Non Native Balance is approximately equal: {non_native_is_eq}")
        if not non_native_is_eq:
            print(f"{prod_non_native} != {stag_non_native}")
        print(f"Stake Ratio is approximately equal: {stake_is_eq}")
        if not stake_is_eq:
            print(f"{prod_stake_ratio} != {stag_stake_ratio}")
