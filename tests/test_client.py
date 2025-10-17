import pytest
import logging
import json
import unittest.mock
from unittest.mock import Mock, patch, mock_open, MagicMock
from md_to_conf import ConfluenceApiClient
from md_to_conf.client import PageInfo, LabelInfo, CheckedResponse
import requests


class TestConfluenceApiClient:
    """Test class for ConfluenceApiClient"""

    @pytest.fixture
    def test_client(self):
        return ConfluenceApiClient(
            "https://domain.confluence.net/wiki", "user", "key", "PO", 2, True
        )

    @pytest.fixture
    def test_client_no_ssl(self):
        return ConfluenceApiClient(
            "https://domain.confluence.net/wiki", "user", "key", "PO", 2, False
        )

    def test_client_init(self):
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
        assert client.space_id == -1
        assert client.space_home_page_id == -1

    def test_client_init_no_ssl(self):
        api_key = "key"
        url = "https://domain.confluence.net/wiki"
        username = "user"
        space_key = "PO"
        editor_version = 2

        client = ConfluenceApiClient(url, username, api_key, space_key, editor_version, False)

        assert not client.use_ssl

    def test_get_session_default(self, test_client):
        session = test_client.get_session()
        assert session.headers.get("Content-Type") == "application/json"
        assert session.auth == ("user", "key")

    def test_get_session_no_json(self, test_client):
        session = test_client.get_session(json=False)
        assert session.headers.get("Content-Type") is None
        assert session.auth == ("user", "key")

    @patch('requests.Session')
    def test_get_session_with_retry_ssl(self, mock_session_class, test_client):
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        session = test_client.get_session(retry=True)
        
        mock_session.mount.assert_called_with("https://", unittest.mock.ANY)

    @patch('requests.Session')
    def test_get_session_with_retry_no_ssl(self, mock_session_class, test_client_no_ssl):
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        session = test_client_no_ssl.get_session(retry=True)
        
        mock_session.mount.assert_called_with("http://", unittest.mock.ANY)

    def test_log_not_found(self, caplog, test_client):
        with caplog.at_level(logging.ERROR):
            test_client.log_not_found("test", {"Page Id": "0"})
        assert len(caplog.records) == 4
        assert "test not found." == caplog.records[0].message
        assert "\tPage Id: 0" == caplog.records[3].message

    def test_check_errors_and_get_json_success(self, test_client):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status.return_value = None
        
        result = test_client.check_errors_and_get_json(mock_response)
        
        assert result.status_code == 200
        assert result.data == {"key": "value"}

    def test_check_errors_and_get_json_404(self, test_client):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.RequestException()
        
        result = test_client.check_errors_and_get_json(mock_response)
        
        assert result.status_code == 404
        assert result.data == {"error": "Not Found"}

    @patch('sys.exit')
    def test_check_errors_and_get_json_server_error(self, mock_exit, test_client):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.content = b"Internal Server Error"
        mock_response.raise_for_status.side_effect = requests.RequestException()
        
        test_client.check_errors_and_get_json(mock_response)
        
        mock_exit.assert_called_once_with(1)

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    def test_get_space_id_success(self, mock_check_errors, mock_get_session, test_client):
        mock_response = CheckedResponse(200, {
            "results": [{"id": "12345", "homepageId": "67890"}]
        })
        mock_check_errors.return_value = mock_response
        
        space_id = test_client.get_space_id()
        
        assert space_id == 12345
        assert test_client.space_home_page_id == 67890

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'log_not_found')
    def test_get_space_id_not_found(self, mock_log_not_found, mock_check_errors, mock_get_session, test_client):
        mock_response = CheckedResponse(404, {"error": "Not Found"})
        mock_check_errors.return_value = mock_response
        
        space_id = test_client.get_space_id()
        
        assert space_id == -1
        mock_log_not_found.assert_called_once_with("Space", {"Space Key": "PO"})

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    def test_get_space_id_cached(self, mock_check_errors, mock_get_session, test_client):
        test_client.space_id = 999
        
        space_id = test_client.get_space_id()
        
        assert space_id == 999
        mock_check_errors.assert_not_called()

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'get_space_id')
    def test_get_page_success(self, mock_get_space_id, mock_check_errors, mock_get_session, test_client):
        mock_get_space_id.return_value = 12345
        mock_response = CheckedResponse(200, {
            "results": [{
                "id": "98765",
                "spaceId": "12345",
                "version": {"number": 1},
                "_links": {"webui": "/spaces/PO/pages/98765/Test+Page"}
            }]
        })
        mock_check_errors.return_value = mock_response
        
        page = test_client.get_page("Test Page")
        
        assert page.id == 98765
        assert page.spaceId == 12345
        assert page.version == 1
        assert page.link == "https://domain.confluence.net/wiki/spaces/PO/pages/98765/Test+Page"

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'get_space_id')
    @patch.object(ConfluenceApiClient, 'log_not_found')
    def test_get_page_not_found(self, mock_log_not_found, mock_get_space_id, mock_check_errors, mock_get_session, test_client):
        mock_get_space_id.return_value = 12345
        mock_response = CheckedResponse(404, {"error": "Not Found"})
        mock_check_errors.return_value = mock_response
        
        page = test_client.get_page("Nonexistent Page")
        
        assert page.id == 0
        assert page.spaceId == 0
        assert page.version == 0
        assert page.link == ""
        mock_log_not_found.assert_called_once_with("Page", {"Space Id": "12345"})

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'get_space_id')
    def test_get_page_empty_results(self, mock_get_space_id, mock_check_errors, mock_get_session, test_client):
        mock_get_space_id.return_value = 12345
        mock_response = CheckedResponse(200, {"results": []})
        mock_check_errors.return_value = mock_response
        
        page = test_client.get_page("Empty Results")
        
        assert page.id == 0

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'get_space_id')
    def test_get_folder_success(self, mock_get_space_id, mock_check_errors, mock_get_session, test_client):
        mock_get_space_id.return_value = 12345
        test_client.space_home_page_id = 123
        mock_response = CheckedResponse(200, {
            "results": [
                {"id": "456", "title": "Test Folder", "type": "folder"}
            ],
            "_links": {
                "base": None,
                "next": None
            }
        })
        mock_check_errors.return_value = mock_response
        
        folder_id = test_client.get_folder("Test Folder")
        
        assert folder_id == 456

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'get_space_id')
    def test_get_folder_not_found(self, mock_get_space_id, mock_check_errors, mock_get_session, test_client):
        mock_get_space_id.return_value = 12345
        test_client.space_home_page_id = 123
        mock_response = CheckedResponse(200, {
            "results": [
                {"id": "456", "title": "Other Folder", "type": "folder"}
            ],
            "_links": {
                "base": None,
                "next": None
            }
        })
        mock_check_errors.return_value = mock_response
        
        folder_id = test_client.get_folder("Nonexistent Folder")
        
        assert folder_id == 0

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'get_space_id')
    @patch.object(ConfluenceApiClient, 'log_not_found')
    def test_get_folder_404(self, mock_log_not_found, mock_get_space_id, mock_check_errors, mock_get_session, test_client):
        mock_get_space_id.return_value = 12345
        test_client.space_home_page_id = 123
        mock_response = CheckedResponse(404, {"error": "Not Found"})
        mock_check_errors.return_value = mock_response
        
        folder_id = test_client.get_folder("Test Folder")
        
        assert folder_id == 0

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'get_space_id')
    def test_get_folder_with_pagination(self, mock_get_space_id, mock_check_errors, mock_get_session, test_client):
        mock_get_space_id.return_value = 12345
        test_client.space_home_page_id = 123
        
        # First call returns page 1 with next link
        first_response = CheckedResponse(200, {
            "results": [
                {"id": "456", "title": "Other Folder", "type": "folder"}
            ],
            "_links": {
                "base": "https://domain.confluence.net/wiki",
                "next": "/api/v2/pages/123/descendants?depth=5&cursor=next_page"
            }
        })
        
        # Second call returns page 2 with target folder and no next link
        second_response = CheckedResponse(200, {
            "results": [
                {"id": "789", "title": "Target Folder", "type": "folder"}
            ],
            "_links": {
                "base": None,
                "next": None
            }
        })
        
        # Set up mock to return different responses on consecutive calls
        mock_check_errors.side_effect = [first_response, second_response]
        
        folder_id = test_client.get_folder("Target Folder")
        
        assert folder_id == 789
        assert mock_check_errors.call_count == 2

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'get_space_id')
    def test_create_page_success(self, mock_get_space_id, mock_check_errors, mock_get_session, test_client):
        mock_get_space_id.return_value = 12345
        mock_response = CheckedResponse(200, {
            "id": "98765",
            "spaceId": "12345",
            "version": {"number": 1},
            "_links": {"webui": "/spaces/PO/pages/98765/New+Page"}
        })
        mock_check_errors.return_value = mock_response
        
        page = test_client.create_page("New Page", "<p>Content</p>", 0)
        
        assert page.id == 98765
        assert page.spaceId == 12345
        assert page.version == 1
        assert page.link == "https://domain.confluence.net/wiki/spaces/PO/pages/98765/New+Page"

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'get_space_id')
    def test_create_page_failure(self, mock_get_space_id, mock_check_errors, mock_get_session, test_client):
        mock_get_space_id.return_value = 12345
        mock_response = CheckedResponse(400, {"error": "Bad Request"})
        mock_check_errors.return_value = mock_response
        
        page = test_client.create_page("Bad Page", "<p>Content</p>", 0)
        
        assert page.id == 0
        assert page.spaceId == 0
        assert page.version == 0
        assert page.link == ""

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'get_space_id')
    def test_update_page_success(self, mock_get_space_id, mock_check_errors, mock_get_session, test_client):
        mock_get_space_id.return_value = 12345
        mock_response = CheckedResponse(200, {
            "_links": {"webui": "/spaces/PO/pages/98765/Updated+Page"}
        })
        mock_check_errors.return_value = mock_response
        
        result = test_client.update_page(98765, "Updated Page", "<p>New Content</p>", 1, 0)
        
        assert result is True

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'get_space_id')
    @patch.object(ConfluenceApiClient, 'log_not_found')
    def test_update_page_not_found(self, mock_log_not_found, mock_get_space_id, mock_check_errors, mock_get_session, test_client):
        mock_get_space_id.return_value = 12345
        mock_response = CheckedResponse(404, {"error": "Not Found"})
        mock_check_errors.return_value = mock_response
        
        result = test_client.update_page(99999, "Nonexistent Page", "<p>Content</p>", 1, 0)
        
        assert result is False
        mock_log_not_found.assert_called_once_with("Page", {"Page Id": "99999"})

    @patch.object(ConfluenceApiClient, 'get_session')
    def test_delete_page_success(self, mock_get_session, test_client):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.raise_for_status.return_value = None
        mock_session.delete.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        test_client.delete_page(98765)
        
        mock_session.delete.assert_called_once_with("https://domain.confluence.net/wiki/api/v2/pages/98765")

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    def test_get_page_properties_success(self, mock_check_errors, mock_get_session, test_client):
        mock_response = CheckedResponse(200, {
            "results": [
                {"key": "editor", "value": "v2"},
                {"key": "custom", "value": "test"}
            ]
        })
        mock_check_errors.return_value = mock_response
        
        properties = test_client.get_page_properties(98765)
        
        assert len(properties) == 2
        assert properties[0]["key"] == "editor"

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'log_not_found')
    def test_get_page_properties_not_found(self, mock_log_not_found, mock_check_errors, mock_get_session, test_client):
        mock_response = CheckedResponse(404, {"error": "Not Found"})
        mock_check_errors.return_value = mock_response
        
        properties = test_client.get_page_properties(99999)
        
        assert properties == []
        mock_log_not_found.assert_called_once_with("Page Properties", {"Page Id": "99999"})

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    def test_update_page_property_new(self, mock_check_errors, mock_get_session, test_client):
        mock_response = CheckedResponse(200, {})
        mock_check_errors.return_value = mock_response
        
        property_data = {"key": "new_prop", "value": "new_value", "version": 1}
        result = test_client.update_page_property(98765, property_data)
        
        assert result is True

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    def test_update_page_property_existing(self, mock_check_errors, mock_get_session, test_client):
        mock_response = CheckedResponse(200, {})
        mock_check_errors.return_value = mock_response
        
        property_data = {"key": "existing_prop", "value": "updated_value", "version": 2, "id": "prop123"}
        result = test_client.update_page_property(98765, property_data)
        
        assert result is True

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    def test_update_page_property_failure(self, mock_check_errors, mock_get_session, test_client):
        mock_response = CheckedResponse(400, {"error": "Bad Request"})
        mock_check_errors.return_value = mock_response
        
        property_data = {"key": "bad_prop", "value": "value", "version": 1}
        result = test_client.update_page_property(98765, property_data)
        
        assert result is False

    @patch.object(ConfluenceApiClient, 'get_session')
    def test_get_attachment_found(self, mock_get_session, test_client):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"results": [{"id": "att123"}]}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        attachment_id = test_client.get_attachment(98765, "test.png")
        
        assert attachment_id == "att123"

    @patch.object(ConfluenceApiClient, 'get_session')
    def test_get_attachment_not_found(self, mock_get_session, test_client):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        attachment_id = test_client.get_attachment(98765, "nonexistent.png")
        
        assert attachment_id == ""

    def test_upload_attachment_http_url(self, test_client):
        result = test_client.upload_attachment(98765, "http://example.com/image.png", "comment")
        assert result is False

    @patch('os.path.isfile')
    def test_upload_attachment_file_not_found(self, mock_isfile, test_client):
        mock_isfile.return_value = False
        
        result = test_client.upload_attachment(98765, "/nonexistent/file.png", "comment")
        
        assert result is False

    @patch('os.path.isfile')
    @patch.object(ConfluenceApiClient, 'get_attachment')
    @patch.object(ConfluenceApiClient, 'get_session')
    @patch('builtins.open', new_callable=mock_open, read_data=b"fake image data")
    def test_upload_attachment_new_file(self, mock_file, mock_get_session, mock_get_attachment, mock_isfile, test_client):
        mock_isfile.return_value = True
        mock_get_attachment.return_value = ""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_session.post.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        result = test_client.upload_attachment(98765, "/path/to/file.png", "comment")
        
        assert result is True

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    def test_get_label_info_found(self, mock_check_errors, mock_get_session, test_client):
        mock_response = CheckedResponse(200, {
            "label": {
                "id": "123",
                "name": "test-label",
                "prefix": "global",
                "label": "Test Label"
            }
        })
        mock_check_errors.return_value = mock_response
        
        label = test_client.get_label_info("test-label")
        
        assert label.id == 123
        assert label.name == "test-label"
        assert label.prefix == "global"
        assert label.label == "Test Label"

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    def test_get_label_info_not_found(self, mock_check_errors, mock_get_session, test_client):
        mock_response = CheckedResponse(404, {"error": "Not Found"})
        mock_check_errors.return_value = mock_response
        
        label = test_client.get_label_info("nonexistent-label")
        
        assert label.id == 0
        assert label.name == ""
        assert label.prefix == ""
        assert label.label == ""

    @patch.object(ConfluenceApiClient, 'get_label_info')
    @patch.object(ConfluenceApiClient, 'get_session')
    def test_add_label_existing_label(self, mock_get_session, mock_get_label_info, test_client):
        mock_get_label_info.return_value = LabelInfo(123, "test-label", "global", "Test Label")
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_session.post.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        result = test_client.add_label(98765, "test-label")
        
        assert result is True

    @patch.object(ConfluenceApiClient, 'get_label_info')
    @patch.object(ConfluenceApiClient, 'get_session')
    def test_add_label_new_label(self, mock_get_session, mock_get_label_info, test_client):
        mock_get_label_info.return_value = LabelInfo(0, "", "", "")
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_session.post.return_value = mock_response
        mock_get_session.return_value = mock_session
        
        result = test_client.add_label(98765, "new-label")
        
        assert result is True

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    @patch.object(ConfluenceApiClient, 'add_label')
    def test_update_labels_success(self, mock_add_label, mock_check_errors, mock_get_session, test_client):
        mock_response = CheckedResponse(200, {
            "results": [
                {"name": "existing-label"},
                {"name": "another-existing-label"}
            ]
        })
        mock_check_errors.return_value = mock_response
        mock_add_label.return_value = True
        
        labels = ["existing-label", "new-label"]
        result = test_client.update_labels(98765, labels)
        
        # Only new-label should be added
        mock_add_label.assert_called_once_with(98765, "new-label")
        assert len(result) == 2

    @patch.object(ConfluenceApiClient, 'get_session')
    @patch.object(ConfluenceApiClient, 'check_errors_and_get_json')
    def test_update_labels_page_not_found(self, mock_check_errors, mock_get_session, test_client):
        mock_response = CheckedResponse(404, {"error": "Not Found"})
        mock_check_errors.return_value = mock_response
        
        labels = ["test-label"]
        result = test_client.update_labels(99999, labels)
        
        assert result is False


# Legacy function-based tests for backwards compatibility
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
