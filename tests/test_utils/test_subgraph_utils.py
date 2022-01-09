from gql import Client

from subgraph.subgraph_utils import make_gql_client, subgraph_url


def test_subgraph_url__happy_path():
    assert "thegraph.com" in subgraph_url("nfts")


def test_subgraph_url__happy_path_from_urls():
    assert "thegraph.com" in subgraph_url("thegraph")


def test_subgraph_url__unhappy_path():
    assert subgraph_url("weird_key") == ""


def test_make_gql_client__happy_path():
    assert type(make_gql_client("nfts")) == Client


def test_make_gql_client__unhappy_path():
    assert not make_gql_client("weird_key")
