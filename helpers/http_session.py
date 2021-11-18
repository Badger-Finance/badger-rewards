from typing import Dict, List, Optional, Union

import requests
from decouple import config
from requests import HTTPError, Response
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


class HTTPClient:
    """
    Wrapper class on top of requests library
    Serves as unwrapper on each HTTP request to avoid boilerplate request.status_code checking

    All method signatures are matching respective requests.HTTP_method()

    For example, self.get(self, url, **kwargs) is mathching requests.get(self, url, **kwargs)
    signature

    Implement more HTTP methods as needed
    """
    def __init__(self, http_session: requests.Session):
        self.http = http_session

    @staticmethod
    def _unwrap_response(response_obj: Response) -> Optional[Union[Dict, List]]:
        if response_obj.ok:
            return response_obj.json()

    def get(self, url, **kwargs) -> Optional[Union[Dict, List]]:
        return self._unwrap_response(
            self.http.get(url, **kwargs)
        )

    def post(self, url, data=None, json=None, **kwargs) -> Optional[Union[Dict, List]]:
        return self._unwrap_response(
            self.http.post(url, data=data, json=json, **kwargs)
        )


http_client = HTTPClient(http)
