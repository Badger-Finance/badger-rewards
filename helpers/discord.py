from discord import Webhook, RequestsWebhookAdapter, Embed
from config.env_config import env_config
import sys

def get_latest_exception_type() -> str:
    err_type, _, _ = sys.exc_info()
    return err_type.__name__
 
    
def send_error_to_discord(msg, issue):
    
    send_message_to_discord(
        f"**{issue}**",
        f":x: {msg}",
        [
            {
                "name": "Error Type",
                "value": get_latest_exception_type(),
                "inline": True,
            },
        ],
        "Error Bot",
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
