import logging
from typing import Optional

from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.requests import log as requests_logger

from subgraph.config import subgraph_urls


def subgraph_url(name: str) -> str:
    if name in subgraph_urls:
        return subgraph_urls[name]
    else:
        return ""


def make_gql_client(name: str) -> Optional[Client]:
    requests_logger.setLevel(logging.WARNING)
    url = subgraph_url(name)
    if not url:
        return
    transport = RequestsHTTPTransport(url=url, retries=3)
    return Client(
        transport=transport, fetch_schema_from_transport=True, execute_timeout=30
    )
