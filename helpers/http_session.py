import requests
from decouple import config
from requests import HTTPError
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from helpers.discord import send_message_to_discord

# setup retry adapter for shared requests session
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)


def status_hook(response, *args, **kwargs):

    # setup status code check for shared requests session
    try:
        response.raise_for_status()
    except HTTPError:
        send_message_to_discord(
            "Request failed",
            f"URL Called: {response.url}",
            [],
            "Rewards Bot",
            url=config("DISCORD_WEBHOOK_URL"),
        )
        return


http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)
http.hooks["response"] = [status_hook]
