from discord import Webhook, RequestsWebhookAdapter, Embed
from rewards.aws.helpers import get_secret

def send_message_to_discord(title: str, description: str, fields: list, url: str, username: str):
    webhook = Webhook.from_url(
        get_secret(url, "DISCORD_WEBHOOK_URL"),
        adapter=RequestsWebhookAdapter(),
    )

    embed = Embed(
        title=title,
        description=description
    )

    for field in fields:
        embed.add_field(name=field.get("name"), value=field.get("value"), inline=field.get("inline"))
    
    webhook.send(embed=embed, username=username)