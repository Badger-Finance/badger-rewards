from discord import Embed, RequestsWebhookAdapter, Webhook
from rich import console
from rich.console import Console

from config.singletons import env_config
from helpers.constants import MONITORING_SECRET_NAMES
from helpers.enums import BotType
from rewards.aws.helpers import get_secret

console = Console()

def send_error_to_discord(e: Exception, error_msg: str, error_type: str, chain: str):
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
        get_discord_url(chain, bot_type=BotType.Boost),
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


def send_code_block_to_discord(
    msg: str, username: str, url: str = env_config.get_webhook_url()
):
    webhook = Webhook.from_url(
        url,
        adapter=RequestsWebhookAdapter(),
    )
    msg = f"```\n{msg}\n```"
    webhook.send(username=username, content=msg)


def get_discord_url(chain: str, bot_type: str = BotType.Cycle) -> str:
    environment = env_config.get_environment()
    return get_secret(
        MONITORING_SECRET_NAMES[environment][chain][bot_type],
        "DISCORD_WEBHOOK_URL",
        kube=env_config.kube,
    )

def console_and_discord(msg: str, chain: str, bot_type: BotType = BotType.Cycle):
    url = get_discord_url(chain, bot_type)
    console.log(msg)
    send_message_to_discord("Rewards Cycle", msg, [], "Rewards Bot", url=url)
