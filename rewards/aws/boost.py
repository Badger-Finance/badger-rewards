from helpers.discord import send_message_to_discord
from rewards.aws.helpers import s3, get_bucket
from config.env_config import env_config
from rich.console import Console
import json

console = Console()
boost_file_name = "badger-boosts.json"


def upload_boosts(boost_data):
    """Upload boosts file to aws bucket

    :param test:
    :param boost_data: calculated boost information
    """

    buckets = ["badger-staging-merkle-proofs"]
    if not env_config.test:
        buckets.append("badger-merkle-proofs")

    for b in buckets:
        console.log(f"Uploading file to s3://{b}/{boost_file_name}")
        s3.put_object(
            Body=str(json.dumps(boost_data)),
            Bucket=b,
            Key=boost_file_name,
            ACL="bucket-owner-full-control",
        )
        console.log(f"✅ Uploaded file to s3://{b}/{boost_file_name}")
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
        )


def download_boosts():
    """Download latest boosts file

    :param test:
    """
    console.log("Downloading boosts ...")
    bucket = get_bucket(env_config.test)
    s3ClientObj = s3.get_object(Bucket=bucket, Key=boost_file_name)
    data = json.loads(s3ClientObj["Body"].read().decode("utf-8"))
    console.log(f"Fetched {len(data['userData'])} boosts")
    return data


def add_user_data(user_data):
    """Upload users boost information

    :param test:
    :param user_data: user boost data
    """
    old_boosts = download_boosts()
    boosts = {"userData": {}, "multiplierData": old_boosts["multiplierData"]}
    for user, data in user_data.items():
        if user in old_boosts["userData"]:
            multipliers = old_boosts["userData"][user]["multipliers"]
        else:
            multipliers = {}

        boosts["userData"][user] = {
            "boost": data["boost"],
            "nativeBalance": data["nativeBalance"],
            "nonNativeBalance": data["nonNativeBalance"],
            "stakeRatio": data["stakeRatio"],
            "multipliers": multipliers,
        }

    with open("badger-boosts.json", "w") as fp:
        json.dump(boosts, fp, indent=4)

    upload_boosts(boosts)


def add_multipliers(multiplier_data, user_multipliers):
    """Upload sett and user multipliers

    :param test:
    :param multiplier_data: sett multipliers
    :param user_multipliers: user multipliers
    """
    boosts = download_boosts()
    boosts["multiplierData"] = {**boosts["multiplierData"], **multiplier_data}
    for user in list(boosts["userData"].keys()):
        if user in user_multipliers:
            boosts["userData"][user]["multipliers"] = user_multipliers[user]

    upload_boosts(boosts)
