from re import sub
from typing import Optional

from gql import Client
from gql.transport.requests import RequestsHTTPTransport

from config.singletons import env_config
from helpers.enums import Environment
from subgraph.config import subgraph_urls


def subgraph_url(name: str) -> str:
    prod_urls = subgraph_urls[Environment.Production]
    staging_urls = subgraph_urls[Environment.Staging]
    if env_config.production:
        return prod_urls.get(name, "")
    else:
        return staging_urls.get(name, prod_urls.get(name, ""))


def make_gql_client(name: str) -> Optional[Client]:
    url = subgraph_url(name)
    if not url:
        return
    transport = RequestsHTTPTransport(url=url, retries=3)
    return Client(
        transport=transport, fetch_schema_from_transport=True, execute_timeout=30
    )
