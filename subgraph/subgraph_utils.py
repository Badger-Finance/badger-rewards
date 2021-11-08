from subgraph.config import subgraph_ids, subgraph_urls
from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport
from config.singletons import env_config


def subgraph_url(name):
    if name in subgraph_ids:
        api_key = env_config.graph_api_key
        id = subgraph_ids[name]
        return f"https://gateway.thegraph.com/api/{api_key}/subgraphs/id/{id}"
    elif name in subgraph_urls:
        return subgraph_urls[name]
    else:
        return ""


def make_gql_client(name):
    url = subgraph_url(name)
    transport = AIOHTTPTransport(url=url)
    return Client(
        transport=transport, fetch_schema_from_transport=True, execute_timeout=30
    )
