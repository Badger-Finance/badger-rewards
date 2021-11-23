from typing import Optional

from gql import Client
from gql.transport.requests import RequestsHTTPTransport

from config.singletons import env_config
from subgraph.config import subgraph_ids, subgraph_urls


def subgraph_url(name: str) -> str:
    if name in subgraph_ids:
        api_key = env_config.graph_api_key
        subgraph_id = subgraph_ids[name]
        return f"https://gateway.thegraph.com/api/{api_key}/subgraphs/id/{subgraph_id}"
    elif name in subgraph_urls:
        return subgraph_urls[name]
    else:
        return ""


def make_gql_client(name: str) -> Optional[Client]:
    url = subgraph_url(name)
    if not url:
        return
    transport = RequestsHTTPTransport(url=url, retries=3)
    return Client(
        transport=transport, fetch_schema_from_transport=True, execute_timeout=30
    )
