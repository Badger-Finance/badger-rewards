from urllib.parse import urlparse

from gql import Client

from helpers.enums import Environment
from subgraph.config import subgraph_urls
from subgraph.subgraph_utils import make_gql_client, subgraph_url


def test_subgraph_url__happy_path():
    url = subgraph_url("nfts")
    host = urlparse(url).hostname
    assert url in subgraph_urls[Environment.Production].values()
    assert host.endswith(".thegraph.com")


def test_subgraph_url__happy_path_from_urls():
    url = subgraph_url("thegraph")
    host = urlparse(url).hostname
    assert url in subgraph_urls[Environment.Production].values()
    assert host.endswith(".thegraph.com")


def test_subgraph_url__unhappy_path():
    assert subgraph_url("weird_key") == ""


def test_make_gql_client__happy_path():
    assert type(make_gql_client("nfts")) == Client


def test_make_gql_client__unhappy_path():
    assert not make_gql_client("weird_key")
