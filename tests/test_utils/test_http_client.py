import pytest
import requests
import responses

from helpers.http_client import HTTPClient, http_client


@responses.activate
@pytest.mark.parametrize(
    'http_method', ["get", "post"]
)
def test_http_client__returns_none_on_err(mock_discord, http_method):
    url = "https://api.etherscan.io/api?module=block&action=" \
          "getblocknobytime&timestamp=123&closest=before&apikey="
    responses.add(
        http_method.upper(), url,
        json={"some": "payload"}, status=404
    )
    assert getattr(http_client, http_method)(url) is None


@responses.activate
@pytest.mark.parametrize(
    'http_method', ["get", "post"]
)
def test_http_client__returns_valid_response(mock_discord, http_method):
    url = "https://api.etherscan.io/api?module=block&action=" \
          "getblocknobytime&timestamp=123&closest=before&apikey="
    responses.add(
        http_method.upper(), url,
        json={"some": "payload"}, status=200
    )
    assert getattr(http_client, http_method)(url) == {"some": "payload"}


def test_invalid_injected_http():
    with pytest.raises(AssertionError):
        HTTPClient(requests.Request)  # noqa
