from typing import Dict, List, Optional, Union

import requests
from requests import Response

from helpers.http_session import http


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
        assert type(self.http) == requests.Session

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
