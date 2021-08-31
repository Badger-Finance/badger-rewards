from discord import Webhook, RequestsWebhookAdapter, Embed
from config.env_config import env_config
from rewards.aws.helpers import get_secret


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
