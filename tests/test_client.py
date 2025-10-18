import pytest
import logging
from unittest.mock import Mock, patch, mock_open
from md_to_conf import ConfluenceApiClient
from md_to_conf.client import LabelInfo, CheckedResponse
import requests


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


def test_get_session_with_retry(test_client):
    session = test_client.get_session(retry=True)
    assert session.headers.get("Content-Type") == "application/json"
    assert session.auth == ("user", "key")


def test_get_session_without_json(test_client):
    session = test_client.get_session(json=False)
    assert "Content-Type" not in session.headers
    assert session.auth == ("user", "key")


def test_get_session_with_ssl_disabled():
    client = ConfluenceApiClient(
        "http://domain.confluence.net/wiki", "user", "key", "PO", 2, False
    )
    session = client.get_session(retry=True)
    assert session.auth == ("user", "key")


def test_check_errors_and_get_json_success(test_client):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 123}
    mock_response.raise_for_status.return_value = None

    result = test_client.check_errors_and_get_json(mock_response)
    assert result.status_code == 200
    assert result.data == {"id": 123}


def test_check_errors_and_get_json_404(test_client):
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.HTTPError()

    result = test_client.check_errors_and_get_json(mock_response)
    assert result.status_code == 404
    assert result.data == {"error": "Not Found"}


def test_check_errors_and_get_json_other_error(test_client):
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.content = b"Server Error"
    mock_response.raise_for_status.side_effect = requests.HTTPError()

    with pytest.raises(SystemExit):
        test_client.check_errors_and_get_json(mock_response)


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
def test_get_space_id_success(mock_check_errors, mock_get_session, test_client):
    mock_session = Mock()
    mock_get_session.return_value = mock_session

    mock_check_errors.return_value = CheckedResponse(
        200, {"results": [{"id": "12345", "homepageId": "67890"}]}
    )

    space_id = test_client.get_space_id()
    assert space_id == 12345
    assert test_client.space_home_page_id == 67890


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
def test_get_space_id_cached(mock_check_errors, mock_get_session, test_client):
    test_client.space_id = 999
    space_id = test_client.get_space_id()
    assert space_id == 999
    mock_check_errors.assert_not_called()


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.log_not_found")
def test_get_space_id_not_found(
    mock_log_not_found, mock_check_errors, mock_get_session, test_client
):
    mock_check_errors.return_value = CheckedResponse(404, {})

    space_id = test_client.get_space_id()
    assert space_id == -1
    mock_log_not_found.assert_called_once_with("Space", {"Space Key": "PO"})


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.get_space_id")
def test_create_page_success(
    mock_get_space_id, mock_check_errors, mock_get_session, test_client
):
    mock_get_space_id.return_value = 12345
    mock_check_errors.return_value = CheckedResponse(
        200,
        {
            "id": "98765",
            "spaceId": "12345",
            "version": {"number": 1},
            "_links": {"webui": "/spaces/PO/pages/98765"},
        },
    )

    result = test_client.create_page("Test Page", "<p>Content</p>", 111)
    assert result.id == 98765
    assert result.spaceId == 12345
    assert result.version == 1
    assert result.link == "https://domain.confluence.net/wiki/spaces/PO/pages/98765"


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.get_space_id")
def test_create_page_failure(
    mock_get_space_id, mock_check_errors, mock_get_session, test_client
):
    mock_get_space_id.return_value = 12345
    mock_check_errors.return_value = CheckedResponse(400, {})

    result = test_client.create_page("Test Page", "<p>Content</p>", 111)
    assert result.id == 0
    assert result.spaceId == 0
    assert result.version == 0
    assert result.link == ""


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.get_space_id")
@patch("md_to_conf.client.ConfluenceApiClient.log_not_found")
def test_update_page_success(
    mock_log_not_found,
    mock_get_space_id,
    mock_check_errors,
    mock_get_session,
    test_client,
):
    mock_get_space_id.return_value = 12345
    mock_check_errors.return_value = CheckedResponse(
        200, {"_links": {"webui": "/spaces/PO/pages/98765"}}
    )

    result = test_client.update_page(
        98765, "Updated Page", "<p>New Content</p>", 1, 111
    )
    assert result is True


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.get_space_id")
@patch("md_to_conf.client.ConfluenceApiClient.log_not_found")
def test_update_page_not_found(
    mock_log_not_found,
    mock_get_space_id,
    mock_check_errors,
    mock_get_session,
    test_client,
):
    mock_get_space_id.return_value = 12345
    mock_check_errors.return_value = CheckedResponse(404, {})

    result = test_client.update_page(
        98765, "Updated Page", "<p>New Content</p>", 1, 111
    )
    assert result is False
    mock_log_not_found.assert_called_once_with("Page", {"Page Id": "98765"})


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.get_space_id")
def test_update_page_other_error(
    mock_get_space_id, mock_check_errors, mock_get_session, test_client
):
    mock_get_space_id.return_value = 12345
    mock_check_errors.return_value = CheckedResponse(400, {})

    result = test_client.update_page(
        98765, "Updated Page", "<p>New Content</p>", 1, 111
    )
    assert result is None


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
def test_delete_page_success(mock_get_session, test_client):
    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 204
    mock_response.raise_for_status.return_value = None
    mock_session.delete.return_value = mock_response
    mock_get_session.return_value = mock_session

    test_client.delete_page(98765)
    mock_session.delete.assert_called_once_with(
        "https://domain.confluence.net/wiki/api/v2/pages/98765"
    )


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
def test_delete_page_failure(mock_get_session, test_client):
    """Test delete_page when status code is not 204 (line 297)"""
    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 400  # Not 204
    mock_response.raise_for_status.return_value = None
    mock_session.delete.return_value = mock_response
    mock_get_session.return_value = mock_session

    test_client.delete_page(98765)
    mock_session.delete.assert_called_once_with(
        "https://domain.confluence.net/wiki/api/v2/pages/98765"
    )


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.get_space_id")
@patch("md_to_conf.client.ConfluenceApiClient.log_not_found")
def test_get_page_success(
    mock_log_not_found,
    mock_get_space_id,
    mock_check_errors,
    mock_get_session,
    test_client,
):
    mock_get_space_id.return_value = 12345
    mock_check_errors.return_value = CheckedResponse(
        200,
        {
            "results": [
                {
                    "id": "98765",
                    "spaceId": "12345",
                    "version": {"number": 2},
                    "_links": {"webui": "/spaces/PO/pages/98765"},
                }
            ]
        },
    )

    result = test_client.get_page("Test Page")
    assert result.id == 98765
    assert result.spaceId == 12345
    assert result.version == 2
    assert result.link == "https://domain.confluence.net/wiki/spaces/PO/pages/98765"


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.get_space_id")
@patch("md_to_conf.client.ConfluenceApiClient.log_not_found")
def test_get_page_not_found(
    mock_log_not_found,
    mock_get_space_id,
    mock_check_errors,
    mock_get_session,
    test_client,
):
    mock_get_space_id.return_value = 12345
    mock_check_errors.return_value = CheckedResponse(404, {})

    result = test_client.get_page("Test Page")
    assert result.id == 0
    assert result.spaceId == 0
    assert result.version == 0
    assert result.link == ""
    mock_log_not_found.assert_called_once_with("Page", {"Space Id": "12345"})


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.log_not_found")
def test_get_page_properties_success(
    mock_log_not_found, mock_check_errors, mock_get_session, test_client
):
    mock_check_errors.return_value = CheckedResponse(
        200, {"results": [{"key": "test", "value": "value"}]}
    )

    result = test_client.get_page_properties(98765)
    assert result == [{"key": "test", "value": "value"}]


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.log_not_found")
def test_get_page_properties_not_found(
    mock_log_not_found, mock_check_errors, mock_get_session, test_client
):
    mock_check_errors.return_value = CheckedResponse(404, {})

    result = test_client.get_page_properties(98765)
    assert result == []
    mock_log_not_found.assert_called_once_with("Page Properties", {"Page Id": "98765"})


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.get_space_id")
@patch("md_to_conf.client.ConfluenceApiClient.log_not_found")
def test_get_folder_success(
    mock_log_not_found,
    mock_get_space_id,
    mock_check_errors,
    mock_get_session,
    test_client,
):
    mock_get_space_id.return_value = 12345
    test_client.space_home_page_id = 67890

    mock_check_errors.return_value = CheckedResponse(
        200,
        {
            "results": [
                {"title": "Test Folder", "type": "folder", "id": "54321"},
                {"title": "Other Page", "type": "page", "id": "11111"},
            ],
            "_links": {},
        },
    )

    result = test_client.get_folder("Test Folder")
    assert result == 54321


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.get_space_id")
@patch("md_to_conf.client.ConfluenceApiClient.log_not_found")
def test_get_folder_not_found(
    mock_log_not_found,
    mock_get_space_id,
    mock_check_errors,
    mock_get_session,
    test_client,
):
    mock_get_space_id.return_value = 12345
    test_client.space_home_page_id = 67890

    mock_check_errors.return_value = CheckedResponse(404, {})

    result = test_client.get_folder("Test Folder")
    assert result == 0
    mock_log_not_found.assert_called_once_with(
        "Folder", {"Space Home Page Id": "67890"}
    )


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.get_space_id")
def test_get_folder_with_pagination(
    mock_get_space_id, mock_check_errors, mock_get_session, test_client
):
    mock_get_space_id.return_value = 12345
    test_client.space_home_page_id = 67890

    # First call returns pagination
    mock_check_errors.side_effect = [
        CheckedResponse(
            200,
            {
                "results": [{"title": "Other Page", "type": "page", "id": "11111"}],
                "_links": {
                    "base": "https://domain.confluence.net/wiki",
                    "next": "/api/v2/pages/67890/descendants?cursor=abc",
                },
            },
        ),
        CheckedResponse(
            200,
            {
                "results": [{"title": "Test Folder", "type": "folder", "id": "54321"}],
                "_links": {},
            },
        ),
    ]

    result = test_client.get_folder("Test Folder")
    assert result == 54321


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
def test_update_page_property_new_property(
    mock_check_errors, mock_get_session, test_client
):
    mock_check_errors.return_value = CheckedResponse(200, {})
    page_property = {"key": "test", "value": "value", "version": 1}

    result = test_client.update_page_property(98765, page_property)
    assert result is True


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
def test_update_page_property_existing_property(
    mock_check_errors, mock_get_session, test_client
):
    mock_check_errors.return_value = CheckedResponse(200, {})
    page_property = {"id": "prop123", "key": "test", "value": "value", "version": 1}

    result = test_client.update_page_property(98765, page_property)
    assert result is True


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
def test_update_page_property_failure(mock_check_errors, mock_get_session, test_client):
    mock_check_errors.return_value = CheckedResponse(400, {})
    page_property = {"key": "test", "value": "value", "version": 1}

    result = test_client.update_page_property(98765, page_property)
    assert result is False


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
def test_get_attachment_found(mock_check_errors, mock_get_session, test_client):
    mock_check_errors.return_value = CheckedResponse(200, {"results": [{"id": "att123"}]})

    result = test_client.get_attachment(98765, "test.png")
    assert result == "att123"


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.log_not_found")
def test_get_attachment_not_found_404(mock_log_not_found, mock_check_errors, mock_get_session, test_client):
    """Test get_attachment when response is 404"""
    mock_check_errors.return_value = CheckedResponse(404, {})

    result = test_client.get_attachment(98765, "test.png")
    assert result == ""
    mock_log_not_found.assert_called_once_with("Attachment", {"Page Id": "98765", "Filename": "test.png"})


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
def test_get_attachment_empty_results(mock_check_errors, mock_get_session, test_client):
    """Test get_attachment when results list is empty (lines 485-487)"""
    mock_check_errors.return_value = CheckedResponse(200, {"results": []})

    result = test_client.get_attachment(98765, "test.png")
    assert result == ""


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.get_attachment")
@patch("os.path.isfile")
@patch("mimetypes.guess_type")
@patch("builtins.open", new_callable=mock_open, read_data=b"file content")
def test_upload_attachment_new_file(
    mock_file,
    mock_guess_type,
    mock_isfile,
    mock_get_attachment,
    mock_get_session,
    test_client,
):
    mock_isfile.return_value = True
    mock_guess_type.return_value = ("image/png", None)
    mock_get_attachment.return_value = ""
    mock_session = Mock()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_session.post.return_value = mock_response
    mock_get_session.return_value = mock_session

    result = test_client.upload_attachment(
        98765, "/path/to/test.png", "Test attachment"
    )
    assert result is True


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.get_attachment")
@patch("os.path.isfile")
@patch("mimetypes.guess_type")
@patch("builtins.open", new_callable=mock_open, read_data=b"file content")
def test_upload_attachment_existing_file(
    mock_file,
    mock_guess_type,
    mock_isfile,
    mock_get_attachment,
    mock_get_session,
    test_client,
):
    mock_isfile.return_value = True
    mock_guess_type.return_value = ("image/png", None)
    mock_get_attachment.return_value = "att123"
    mock_session = Mock()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_session.post.return_value = mock_response
    mock_get_session.return_value = mock_session

    result = test_client.upload_attachment(
        98765, "/path/to/test.png", "Test attachment"
    )
    assert result is True


def test_upload_attachment_http_url(test_client):
    result = test_client.upload_attachment(
        98765, "http://example.com/test.png", "Test attachment"
    )
    assert result is False


@patch("os.path.isfile")
def test_upload_attachment_file_not_found(mock_isfile, test_client):
    mock_isfile.return_value = False

    result = test_client.upload_attachment(
        98765, "/path/to/missing.png", "Test attachment"
    )
    assert result is False


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
def test_get_label_info_found(mock_check_errors, mock_get_session, test_client):
    mock_check_errors.return_value = CheckedResponse(
        200,
        {
            "label": {
                "id": "123",
                "name": "test-label",
                "prefix": "global",
                "label": "Test Label",
            }
        },
    )

    result = test_client.get_label_info("test-label")
    assert result.id == 123
    assert result.name == "test-label"
    assert result.prefix == "global"
    assert result.label == "Test Label"


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
def test_get_label_info_not_found(mock_check_errors, mock_get_session, test_client):
    mock_check_errors.return_value = CheckedResponse(404, {})

    result = test_client.get_label_info("test-label")
    assert result.id == 0
    assert result.name == ""
    assert result.prefix == ""
    assert result.label == ""


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.get_label_info")
def test_add_label_existing_label(mock_get_label_info, mock_get_session, test_client):
    mock_get_label_info.return_value = LabelInfo(
        123, "test-label", "custom", "Test Label"
    )
    mock_session = Mock()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_session.post.return_value = mock_response
    mock_get_session.return_value = mock_session

    result = test_client.add_label(98765, "test-label")
    assert result is True


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.get_label_info")
def test_add_label_new_label(mock_get_label_info, mock_get_session, test_client):
    mock_get_label_info.return_value = LabelInfo(0, "", "", "")
    mock_session = Mock()
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_session.post.return_value = mock_response
    mock_get_session.return_value = mock_session

    result = test_client.add_label(98765, "new-label")
    assert result is True


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
@patch("md_to_conf.client.ConfluenceApiClient.add_label")
def test_update_labels_success(
    mock_add_label, mock_check_errors, mock_get_session, test_client
):
    mock_check_errors.return_value = CheckedResponse(
        200, {"results": [{"name": "existing-label"}, {"name": "another-label"}]}
    )
    mock_add_label.return_value = True

    result = test_client.update_labels(98765, ["existing-label", "new-label"])
    mock_add_label.assert_called_once_with(98765, "new-label")
    assert len(result) == 2


@patch("md_to_conf.client.ConfluenceApiClient.get_session")
@patch("md_to_conf.client.ConfluenceApiClient.check_errors_and_get_json")
def test_update_labels_page_not_found(mock_check_errors, mock_get_session, test_client):
    mock_check_errors.return_value = CheckedResponse(404, {})

    result = test_client.update_labels(98765, ["test-label"])
    assert result is False
