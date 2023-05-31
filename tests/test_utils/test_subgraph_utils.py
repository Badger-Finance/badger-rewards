from urllib.parse import urlparse

from gql import Client

from helpers.enums import Environment, SubgraphUrlType
from subgraph.config import subgraph_urls
from subgraph.subgraph_utils import make_gql_client, subgraph_url, subgraph_url_from_config


def test_subgraph_url_from_config__happy_path():
    urlDict = subgraph_url_from_config("thegraph")
    url = urlDict[SubgraphUrlType.Plain]
    host = urlparse(url).hostname
    assert urlDict in subgraph_urls[Environment.Production].values()
    assert host.endswith(".thegraph.com")


def test_subgraph_url_from_config__unhappy_path():
    assert subgraph_url_from_config("weird_key") == ""


def test_make_gql_client__happy_path():
    assert type(make_gql_client("nfts")) == Client


def test_subgraph_url__happy_path():
    url = subgraph_url("tokens_ethereum")
    assert url == "www.thegraph.com/test/value"


def test_subgraph_url__unhappy_path():
    url = subgraph_url("tokens_arbitrum")
    assert url != "www.thegraph.com/test/value"
