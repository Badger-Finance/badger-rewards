import os

from discord import Embed, RequestsWebhookAdapter, Webhook
from rich.console import Console

from config.constants.aws import MONITORING_SECRET_NAMES
from config.singletons import env_config
from helpers.enums import BotType, Network
from rewards.aws.helpers import get_secret


console = Console()


def send_error_to_discord(
    e: Exception,
    error_msg: str,
    error_type: str,
    chain: Network,
):
    send_message_to_discord(
        f"**{error_type}**",
        f":x: {error_msg}",
        [
            {
                "name": "Error Type",
                "value": type(e),
                "inline": True,
            },
            {
                "name": "Error Description",
                "value": e.args,
                "inline": True,
            },
        ],
        "Error Bot",
        get_discord_url(chain),
    )


def send_message_to_discord(
    title: str,
    description: str,
    fields: list,
    username: str,
    url: str = env_config.get_webhook_url(),
):
    webhook = Webhook.from_url(
        url,
        adapter=RequestsWebhookAdapter(),
    )

    embed = Embed(title=title, description=description)

    for field in fields:
        embed.add_field(
            name=field.get("name"), value=field.get("value"), inline=field.get("inline")
        )

    webhook.send(embed=embed, username=username)


def send_plain_text_to_discord(
    message: str,
    username: str,
    url: str = env_config.get_webhook_url(),
):
    webhook = Webhook.from_url(
        url,
        adapter=RequestsWebhookAdapter()
    )
    webhook.send(message, username=username)


def send_code_block_to_discord(
    msg: str, username: str, url: str = env_config.get_webhook_url()
):
    webhook = Webhook.from_url(
        url,
        adapter=RequestsWebhookAdapter(),
    )
    msg = f"```\n{msg}\n```"
    webhook.send(username=username, content=msg)


def get_discord_url(chain: str) -> str:
    bot_type = os.getenv("BOT_TYPE", BotType.Cycle)
    environment = env_config.get_environment()
    return get_secret(
        MONITORING_SECRET_NAMES[environment][chain][bot_type],
        "DISCORD_WEBHOOK_URL",
        kube=env_config.kube,
    )


def console_and_discord(
        msg: str, chain: str, mentions: str = ""
):
    url = get_discord_url(chain)
    console.log(msg)
    if len(mentions) > 0:
        send_plain_text_to_discord(mentions, "Rewards Bot", url=url)
    send_message_to_discord("Rewards Cycle", msg, [], "Rewards Bot", url=url)
