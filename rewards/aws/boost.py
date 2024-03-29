import json
from typing import Dict

from config.constants.chain_mappings import CHAIN_IDS
from config.singletons import env_config
from helpers.discord import get_discord_url
from helpers.discord import send_message_to_discord
from helpers.enums import BucketNames
from logging_utils import logger
from rewards.aws.helpers import get_bucket
from rewards.aws.helpers import s3


def upload_boosts(boost_data, chain: str, cycle: bool = False):
    upload_boosts_to_aws(boost_data, chain, "badger-boosts", cycle)


def upload_proposed_boosts(boost_data, chain: str):
    upload_boosts_to_aws(boost_data, chain, "propose-boosts")


def upload_boosts_to_aws(boost_data, chain: str, file_name: str, cycle: bool = False):
    """Upload boosts file to aws bucket

    :param test:
    :param boost_data: calculated boost information
    """
    discord_url = get_discord_url(chain)
    chain_id = CHAIN_IDS[chain]
    boost_file_name = f"{file_name}-{chain_id}.json"
    buckets = []
    if env_config.test or env_config.staging:
        buckets.append(BucketNames.MerkleStaging)
        with open("test_boost.json", "w") as tree_file:
            json.dump(boost_data, tree_file, indent=4, sort_keys=True)
    elif env_config.production:
        if cycle:
            buckets.append(BucketNames.MerkleStaging)
        buckets.append(BucketNames.MerkleProd)

    for b in buckets:
        logger.info(f"Uploading file to s3://{b}/{boost_file_name}")
        s3.put_object(
            Body=str(json.dumps(boost_data)),
            Bucket=b,
            Key=boost_file_name,
            ACL="bucket-owner-full-control",
        )
        logger.info(f"✅ Uploaded file to s3://{b}/{boost_file_name}")
        send_message_to_discord(
            "**BADGER BOOST UPDATED**",
            f"✅ Uploaded file to s3://{b}/{boost_file_name}",
            [
                {
                    "name": "User Count",
                    "value": len(boost_data["userData"]),
                    "inline": True,
                }
            ],
            "Boost Bot",
            url=discord_url,
        )


def download_boosts(chain: str) -> Dict:
    """Download latest boosts file

    :param test:
    """
    logger.info("Downloading boosts ...")
    chain_id = CHAIN_IDS[chain]

    boost_file_name = f"badger-boosts-{chain_id}.json"
    bucket = get_bucket(env_config.production)
    s3ClientObj = s3.get_object(Bucket=bucket, Key=boost_file_name)
    data = json.loads(s3ClientObj["Body"].read().decode("utf-8"))
    logger.info(f"Fetched {len(data['userData'])} boosts")
    return data


def download_proposed_boosts(chain: str) -> Dict:
    logger.info("Downloading boosts ...")
    chain_id = CHAIN_IDS[chain]

    boost_file_name = f"propose-boosts-{chain_id}.json"
    bucket = get_bucket(env_config.production)
    s3ClientObj = s3.get_object(Bucket=bucket, Key=boost_file_name)
    data = json.loads(s3ClientObj["Body"].read().decode("utf-8"))
    logger.info(f"Fetched {len(data['userData'])} boosts")
    return data


def add_user_data(user_data, chain):
    """Upload users boost information

    :param test:
    :param user_data: user boost data
    """
    old_boosts = download_boosts(chain)
    boosts = {"userData": {}, "multiplierData": old_boosts["multiplierData"]}
    for user, data in user_data.items():
        if user in old_boosts["userData"]:
            if float(old_boosts["userData"][user]["stakeRatio"]) > 0:
                multipliers = old_boosts["userData"][user]["multipliers"]
            else:
                multipliers = {}
        else:
            multipliers = {}

        boosts["userData"][user] = {
            "boost": data["boost"],
            "nativeBalance": str(data["nativeBalance"]),
            "nonNativeBalance": str(data["nonNativeBalance"]),
            "nftBalance": str(data["nftBalance"]),
            "bveCvxBalance": str(data["bveCvxBalance"]),
            "diggBalance": str(data["diggBalance"]),
            "stakeRatio": str(data["stakeRatio"]),
            "multipliers": multipliers,
            "nfts": data.get("nfts", []),
        }
    upload_boosts(boosts, chain)


def add_multipliers(boosts, multiplier_data, user_multipliers):
    """Upload sett and user multipliers

    :param test:
    :param multiplier_data: sett multipliers
    :param user_multipliers: user multipliers
    """
    boosts["multiplierData"] = multiplier_data
    for user in list(boosts["userData"].keys()):
        if user in user_multipliers:
            if float(boosts["userData"][user]["stakeRatio"]) > 0:
                boosts["userData"][user]["multipliers"] = user_multipliers[user]
            else:
                boosts["userData"][user]["multipliers"] = {}
    return boosts
