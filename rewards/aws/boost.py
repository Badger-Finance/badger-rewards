import boto3
from helpers.discord import send_message_to_discord
from rewards.aws.helpers import s3, get_bucket
from config.env_config import env_config
from rich.console import Console
import json

console = Console()

boostsFileName = "badger-boosts.json"

s3 = boto3.client("s3")

def upload_boosts(boostData):
    """Upload boosts file to aws bucket

    :param test:
    :param boostData: calculated boost information
    """
    bucket = get_bucket(env_config.test)
    console.log("Uploading file to s3://{}/{}".format(bucket, boostsFileName))
    s3.put_object(Body=str(json.dumps(boostData)), Bucket=bucket, Key=boostsFileName)
    console.log("✅ Uploaded file to s3://{}/{}".format(bucket, boostsFileName))
    send_message_to_discord(
        "**BADGER BOOST UPDATED**",
        f"✅ Uploaded file to s3://{bucket}/{boostsFileName}",
        [{"name": "User Count", "value": len(boostData["userData"]), "inline": True}],
        "keepers/boostBot",
    )


def download_boosts():
    """Download latest boosts file

    :param test:
    """
    bucket = get_bucket(env_config.test)
    s3ClientObj = s3.get_object(Bucket=bucket, Key=boostsFileName)
    data = json.loads(s3ClientObj["Body"].read().decode("utf-8"))
    return data


def add_user_data(userData):
    """Upload users boost information

    :param test:
    :param userData: user boost data
    """
    oldBoosts = download_boosts()
    boosts = {"userData": {}, "multiplierData": oldBoosts["multiplierData"]}
    for user, data in userData.items():
        if user in oldBoosts["userData"]:
            multipliers = oldBoosts["userData"][user]["multipliers"]
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


def add_multipliers(multiplierData, userMultipliers):
    """Upload sett and user multipliers

    :param test:
    :param multiplierData: sett multipliers
    :param userMultipliers: user multipliers
    """
    boosts = download_boosts()
    boosts["multiplierData"] = {**boosts["multiplierData"], **multiplierData}
    for user in list(boosts["userData"].keys()):
        if user in userMultipliers:
            boosts["userData"][user]["multipliers"] = userMultipliers[user]

    upload_boosts(boosts)
