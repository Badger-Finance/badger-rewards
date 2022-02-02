import logging
from typing import Optional

from gql import Client
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.requests import log as requests_logger

from config.singletons import env_config
from helpers.enums import Environment, Network
from subgraph.config import subgraph_urls
from helpers.discord import send_error_to_discord


def subgraph_url(name: str) -> str:
    prod_urls = subgraph_urls[Environment.Production]
    staging_urls = subgraph_urls[Environment.Staging]
    if env_config.production:
        return prod_urls.get(name, "")
    else:
        return staging_urls.get(name, prod_urls.get(name, ""))


def make_gql_client(name: str) -> Optional[Client]:
    requests_logger.setLevel(logging.WARNING)
    url = subgraph_url(name)
    if not url:
        return
    transport = RequestsHTTPTransport(url=url, retries=3)
    return Client(
        transport=transport, fetch_schema_from_transport=True, execute_timeout=60
    )


class SubgraphClient:
    def __init__(self, name, chain: Network):
        self.client = make_gql_client(name)
        self.chain = chain

    def execute(self, **kwargs):
        transport_url = self.client.transport.url
        try:
            return self.client.execute(**kwargs)
        except Exception as e:
            send_error_to_discord(
                e,
                error_msg=f"Error with subgraph: {transport_url}",
                error_type="Subgraph Error",
                chain=self.chain
            )
            raise e


