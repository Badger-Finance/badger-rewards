import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from config.env_config import EnvConfig

env_config = EnvConfig()

# setup retry adapter for shared requests session
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["GET", "POST"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
# setup status code check for shared requests session
assert_status_hook = lambda response, *args, **kwargs: response.raise_for_status()

http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)
http.hooks["response"] = [assert_status_hook]
