import logging
from typing import Optional

from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.requests import log as requests_logger

from config.singletons import env_config
from helpers.enums import Environment, Network, SubgraphUrlType
from subgraph.config import subgraph_urls
from helpers.discord import send_error_to_discord


def subgraph_url(name: str) -> dict[SubgraphUrlType, str]:
    prod_urls = subgraph_urls[Environment.Production]
    staging_urls = subgraph_urls[Environment.Staging]
    if env_config.production:
        return prod_urls.get(name, "")
    return staging_urls.get(name, prod_urls.get(name, ""))


def make_gql_client(name: str) -> Optional[Client]:
    requests_logger.setLevel(logging.WARNING)
    urlDict = subgraph_url(name)
    url = ""
    if not urlDict:
        return
    if SubgraphUrlType.Plain in urlDict:
        url = urlDict[SubgraphUrlType.Plain]
    elif SubgraphUrlType.AWS in urlDict:
        url = env_config.get_graph_api_key(urlDict[SubgraphUrlType.AWS], "NODE_URL")
    transport = RequestsHTTPTransport(url=url, retries=3)
    return Client(
        transport=transport, fetch_schema_from_transport=True, execute_timeout=60
    )


class SubgraphClient:
    """
    Wrapper around graphql for subgraphs to handle errors
    """
    def __init__(self, name: str, chain: Network):
        self.client = make_gql_client(name)
        self.chain = chain

    def execute(self, *args, **kwargs):
        try:
            return self.client.execute(*args, **kwargs)
        except Exception as error:
            send_error_to_discord(
                error,
                error_msg=f"Error with subgraph: {self.client.transport.url}",
                error_type="Subgraph Error",
                chain=self.chain
            )
            raise error
