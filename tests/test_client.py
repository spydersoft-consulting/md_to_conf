import pytest
import logging
from md_to_conf import ConfluenceApiClient


def test_client_init():
    api_key = "key"
    url = "https://domain.confluence.net/wiki"
    username = "user"
    space_key = "PO"
    editor_version = 2

    client = ConfluenceApiClient(url, username, api_key, space_key, editor_version)

    assert client.api_key == api_key
    assert client.confluence_api_url == url
    assert client.user_name == username
    assert client.space_key == space_key
    assert client.editor_version == editor_version
    assert client.use_ssl


@pytest.fixture
def test_client():
    return ConfluenceApiClient(
        "https://domain.confluence.net/wiki", "user", "key", "PO", 2, True
    )


def test_get_session_default(test_client):
    session = test_client.get_session()
    assert session.headers.get("Content-Type") == "application/json"


def test_log_not_found(caplog, test_client):
    with caplog.at_level(logging.ERROR):
        test_client.log_not_found("test", {"Page Id": "%d" % 0})
    assert len(caplog.records) == 4
    assert "test not found." == caplog.records[0].message
    assert "\tPage Id: 0" == caplog.records[3].message
    
