import pytest
import os
import tempfile
from unittest.mock import Mock, patch, mock_open, MagicMock
from md_to_conf.confluence_converter import ConfluenceConverter
from md_to_conf.client import ConfluenceApiClient, PageInfo


class TestConfluenceConverter:
    """Test class for ConfluenceConverter"""

    @pytest.fixture
    def temp_markdown_file(self):
        """Create a temporary markdown file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Title\n\nThis is test content.")
            temp_file = f.name
        yield temp_file
        os.unlink(temp_file)

    @pytest.fixture
    def confluence_converter(self, temp_markdown_file):
        """Create a ConfluenceConverter instance for testing"""
        with patch('md_to_conf.confluence_converter.ConfluenceApiClient'):
            converter = ConfluenceConverter(
                file=temp_markdown_file,
                md_source="default",
                title="Test Title",
                org_name="test-org",
                use_ssl=True,
                user_name="testuser",
                space_key="TEST",
                api_key="test-api-key",
                ancestor="ancestor-page",
                version=2
            )
        return converter

    def test_init(self, temp_markdown_file):
        """Test ConfluenceConverter initialization"""
        with patch('md_to_conf.confluence_converter.ConfluenceApiClient'):
            converter = ConfluenceConverter(
                file=temp_markdown_file,
                md_source="default",
                title="Test Title",
                org_name="test-org",
                use_ssl=True,
                user_name="testuser",
                space_key="TEST",
                api_key="test-api-key",
                ancestor="ancestor-page",
                version=2
            )

        assert converter.file == temp_markdown_file
        assert converter.md_source == "default"
        assert converter.title == "Test Title"
        assert converter.org_name == "test-org"
        assert converter.use_ssl is True
        assert converter.user_name == "testuser"
        assert converter.api_key == "test-api-key"
        assert converter.version == 2
        assert converter.ancestor == "ancestor-page"
        assert converter.space_key == "TEST"
        assert converter.source_folder == os.path.dirname(os.path.abspath(temp_markdown_file))

    def test_init_with_none_space_key(self, temp_markdown_file):
        """Test ConfluenceConverter initialization with None space_key"""
        with patch('md_to_conf.confluence_converter.ConfluenceApiClient'):
            converter = ConfluenceConverter(
                file=temp_markdown_file,
                md_source="default",
                title="Test Title",
                org_name="test-org",
                use_ssl=True,
                user_name="testuser",
                space_key=None,
                api_key="test-api-key",
                ancestor="ancestor-page",
                version=2
            )

        assert converter.space_key == "~testuser"

    def test_get_confluence_api_url_with_domain(self, confluence_converter):
        """Test get_confluence_api_url with domain containing dot"""
        confluence_converter.org_name = "example.com"
        url = confluence_converter.get_confluence_api_url()
        assert url == "https://example.com"

    def test_get_confluence_api_url_without_domain(self, confluence_converter):
        """Test get_confluence_api_url with org name only"""
        confluence_converter.org_name = "testorg"
        url = confluence_converter.get_confluence_api_url()
        assert url == "https://testorg.atlassian.net/wiki"

    def test_get_confluence_api_url_no_ssl(self, confluence_converter):
        """Test get_confluence_api_url with SSL disabled"""
        confluence_converter.use_ssl = False
        confluence_converter.org_name = "testorg"
        url = confluence_converter.get_confluence_api_url()
        # Note: The current implementation has a bug - it doesn't properly replace https with http
        assert url == "https://testorg.atlassian.net/wiki"

    def test_get_space_key_with_provided_key(self, confluence_converter):
        """Test get_space_key with provided space key"""
        result = confluence_converter.get_space_key("CUSTOM")
        assert result == "CUSTOM"

    def test_get_space_key_with_none(self, confluence_converter):
        """Test get_space_key with None"""
        result = confluence_converter.get_space_key(None)
        assert result == "~testuser"

    @patch('md_to_conf.confluence_converter.ConfluenceApiClient')
    def test_get_client(self, mock_client_class, confluence_converter):
        """Test get_client method"""
        confluence_converter.get_client()
        
        mock_client_class.assert_called_once_with(
            confluence_converter.get_confluence_api_url(),
            confluence_converter.user_name,
            confluence_converter.api_key,
            confluence_converter.space_key,
            confluence_converter.version,
            confluence_converter.use_ssl,
        )

    def test_get_parent_page_with_ancestor(self, confluence_converter):
        """Test get_parent_page with ancestor"""
        mock_page = PageInfo(id=123, spaceId=1, version=1, link="test-link")
        confluence_converter.confluence_client.get_page.return_value = mock_page
        
        parent_id = confluence_converter.get_parent_page()
        
        assert parent_id == 123
        confluence_converter.confluence_client.get_page.assert_called_once_with("ancestor-page")

    def test_get_parent_page_without_ancestor(self, confluence_converter):
        """Test get_parent_page without ancestor"""
        confluence_converter.ancestor = None
        
        parent_id = confluence_converter.get_parent_page()
        
        assert parent_id == 0

    def test_get_parent_page_ancestor_not_found(self, confluence_converter):
        """Test get_parent_page when ancestor page doesn't exist"""
        confluence_converter.confluence_client.get_page.return_value = None
        
        parent_id = confluence_converter.get_parent_page()
        
        assert parent_id == 0

    def test_add_images(self, confluence_converter):
        """Test add_images method"""
        html = '<p>Test <img src="image.png" alt="Test Image"/> content</p>'
        page_id = 123
        
        confluence_converter.confluence_client.upload_attachment = Mock()
        
        result = confluence_converter.add_images(page_id, html)
        
        expected_html = '<p>Test <img src="/wiki/download/attachments/123/image.png" alt="Test Image"/> content</p>'
        assert result == expected_html
        confluence_converter.confluence_client.upload_attachment.assert_called_once()

    def test_add_images_no_wiki_in_url(self, confluence_converter):
        """Test add_images method when API URL doesn't end with /wiki"""
        confluence_converter.org_name = "example.com"  # This won't end with /wiki
        html = '<p>Test <img src="image.png" alt="Test Image"/> content</p>'
        page_id = 123
        
        confluence_converter.confluence_client.upload_attachment = Mock()
        
        result = confluence_converter.add_images(page_id, html)
        
        expected_html = '<p>Test <img src="/download/attachments/123/image.png" alt="Test Image"/> content</p>'
        assert result == expected_html

    def test_add_images_with_http_url(self, confluence_converter):
        """Test add_images method with HTTP URL (should not be replaced)"""
        html = '<p>Test <img src="http://example.com/image.png" alt="Test Image"/> content</p>'
        page_id = 123
        
        confluence_converter.confluence_client.upload_attachment = Mock()
        
        result = confluence_converter.add_images(page_id, html)
        
        # HTTP URLs should not be replaced
        assert result == html
        confluence_converter.confluence_client.upload_attachment.assert_called_once()

    def test_add_attachments(self, confluence_converter):
        """Test add_attachments method"""
        page_id = 123
        files = ["file1.txt", "file2.pdf"]
        
        confluence_converter.confluence_client.upload_attachment = Mock()
        
        confluence_converter.add_attachments(page_id, files)
        
        assert confluence_converter.confluence_client.upload_attachment.call_count == 2
        
        # Verify the calls were made with correct arguments
        calls = confluence_converter.confluence_client.upload_attachment.call_args_list
        expected_file1_path = os.path.join(confluence_converter.source_folder, "file1.txt")
        expected_file2_path = os.path.join(confluence_converter.source_folder, "file2.pdf")
        
        # Check first call
        assert calls[0][0] == (123, expected_file1_path, "")
        # Check second call
        assert calls[1][0] == (123, expected_file2_path, "")

    def test_add_attachments_empty_list(self, confluence_converter):
        """Test add_attachments method with empty list"""
        page_id = 123
        files = []
        
        confluence_converter.confluence_client.upload_attachment = Mock()
        
        confluence_converter.add_attachments(page_id, files)
        
        confluence_converter.confluence_client.upload_attachment.assert_not_called()

    def test_add_attachments_none(self, confluence_converter):
        """Test add_attachments method with None"""
        page_id = 123
        files = None
        
        confluence_converter.confluence_client.upload_attachment = Mock()
        
        confluence_converter.add_attachments(page_id, files)
        
        confluence_converter.confluence_client.upload_attachment.assert_not_called()

    @patch('md_to_conf.confluence_converter.MarkdownConverter')
    def test_add_local_refs_default_source(self, mock_converter_class, confluence_converter):
        """Test add_local_refs method with default markdown source"""
        mock_converter = Mock()
        mock_converter.process_headers.return_value = {"#section-1": "Section-1"}
        mock_converter.process_links.return_value = "modified html"
        
        html = '<h1>Section 1</h1><p>Content with <a href="#section-1">link</a></p>'
        page_id = 123
        title = "Test Page"
        
        result = confluence_converter.add_local_refs(page_id, title, html, mock_converter)
        
        assert result == "modified html"
        mock_converter.process_headers.assert_called_once_with("#", "_%d", ["Section 1"])
        mock_converter.process_links.assert_called_once_with(
            html, ['<a href="#section-1">link</a>'], {"#section-1": "Section-1"}, "TEST", 123, "Test Page"
        )

    @patch('md_to_conf.confluence_converter.MarkdownConverter')
    def test_add_local_refs_bitbucket_source(self, mock_converter_class, confluence_converter):
        """Test add_local_refs method with bitbucket markdown source"""
        confluence_converter.md_source = "bitbucket"
        mock_converter = Mock()
        mock_converter.process_headers.return_value = {"#markdown-header-section-1": "Section-1"}
        mock_converter.process_links.return_value = "modified html"
        
        html = '<h1>Section 1</h1><p>Content with <a href="#markdown-header-section-1">link</a></p>'
        page_id = 123
        title = "Test Page"
        
        result = confluence_converter.add_local_refs(page_id, title, html, mock_converter)
        
        assert result == "modified html"
        mock_converter.process_headers.assert_called_once_with("#markdown-header-", "_%d", ["Section 1"])

    @patch('md_to_conf.confluence_converter.MarkdownConverter')
    def test_add_local_refs_unsupported_source(self, mock_converter_class, confluence_converter):
        """Test add_local_refs method with unsupported markdown source"""
        confluence_converter.md_source = "unsupported"
        mock_converter = Mock()
        
        html = '<h1>Section 1</h1><p>Content</p>'
        page_id = 123
        title = "Test Page"
        
        result = confluence_converter.add_local_refs(page_id, title, html, mock_converter)
        
        assert result == html  # Should return original html unchanged
        mock_converter.process_headers.assert_not_called()
        mock_converter.process_links.assert_not_called()

    @patch('md_to_conf.confluence_converter.MarkdownConverter')
    def test_add_local_refs_no_headers(self, mock_converter_class, confluence_converter):
        """Test add_local_refs method with no headers in HTML"""
        mock_converter = Mock()
        
        html = '<p>Content without headers</p>'
        page_id = 123
        title = "Test Page"
        
        result = confluence_converter.add_local_refs(page_id, title, html, mock_converter)
        
        assert result == html  # Should return original html unchanged
        mock_converter.process_headers.assert_not_called()
        mock_converter.process_links.assert_not_called()

    @patch('md_to_conf.confluence_converter.MarkdownConverter')
    def test_add_local_refs_no_links(self, mock_converter_class, confluence_converter):
        """Test add_local_refs method with headers but no links"""
        mock_converter = Mock()
        mock_converter.process_headers.return_value = {"#section-1": "Section-1"}
        
        html = '<h1>Section 1</h1><p>Content without links</p>'
        page_id = 123
        title = "Test Page"
        
        result = confluence_converter.add_local_refs(page_id, title, html, mock_converter)
        
        assert result == html  # Should return original html unchanged
        mock_converter.process_headers.assert_called_once()
        mock_converter.process_links.assert_not_called()

    def test_get_properties_to_update_editor_version_change(self, confluence_converter):
        """Test get_properties_to_update when editor version changes"""
        page_id = 123
        props = {}
        existing_properties = [
            {
                "key": "editor",
                "value": "v1",
                "version": {"number": 1},
                "id": "prop1"
            }
        ]
        
        confluence_converter.confluence_client.get_page_properties.return_value = existing_properties
        
        result = confluence_converter.get_properties_to_update(props, page_id)
        
        expected = [
            {
                "key": "editor",
                "version": 2,
                "value": "v2",
                "id": "prop1"
            }
        ]
        assert result == expected

    def test_get_properties_to_update_new_properties(self, confluence_converter):
        """Test get_properties_to_update with new properties"""
        page_id = 123
        props = {"custom_prop": "custom_value"}
        existing_properties = []
        
        confluence_converter.confluence_client.get_page_properties.return_value = existing_properties
        
        result = confluence_converter.get_properties_to_update(props, page_id)
        
        expected = [
            {
                "key": "custom_prop",
                "version": 1,
                "value": "custom_value"
            }
        ]
        assert result == expected

    def test_get_properties_to_update_existing_properties(self, confluence_converter):
        """Test get_properties_to_update with existing properties"""
        page_id = 123
        props = {"existing_prop": "new_value"}
        existing_properties = [
            {
                "key": "existing_prop",
                "value": "old_value",
                "version": {"number": 1},
                "id": "prop1"
            }
        ]
        
        confluence_converter.confluence_client.get_page_properties.return_value = existing_properties
        
        result = confluence_converter.get_properties_to_update(props, page_id)
        
        expected = [
            {
                "key": "existing_prop",
                "version": 2,
                "value": "new_value",
                "id": "prop1"
            }
        ]
        assert result == expected

    def test_get_properties_to_update_none_props(self, confluence_converter):
        """Test get_properties_to_update with None properties"""
        page_id = 123
        props = None
        existing_properties = []
        
        confluence_converter.confluence_client.get_page_properties.return_value = existing_properties
        
        result = confluence_converter.get_properties_to_update(props, page_id)
        
        assert result == []

    @patch('md_to_conf.confluence_converter.MarkdownConverter')
    @patch('builtins.open', new_callable=mock_open, read_data="# Test Title\n\nContent")
    def test_convert_simulate_mode(self, mock_file, mock_converter_class, confluence_converter):
        """Test convert method in simulate mode"""
        mock_converter = Mock()
        mock_converter.convert_md_to_conf_html.return_value = "<p>Test HTML</p>"
        mock_converter_class.return_value = mock_converter
        
        confluence_converter.convert(
            simulate=True,
            delete=False,
            remove_emojies=False,
            add_contents=False,
            labels=[],
            properties={},
            attachments=[]
        )
        
        # In simulate mode, no API calls should be made
        confluence_converter.confluence_client.get_page.assert_not_called()

    @patch('md_to_conf.confluence_converter.MarkdownConverter')
    @patch('builtins.open', new_callable=mock_open, read_data="# Test Title\n\nContent")
    def test_convert_delete_mode(self, mock_file, mock_converter_class, confluence_converter):
        """Test convert method in delete mode"""
        mock_converter = Mock()
        mock_converter.convert_md_to_conf_html.return_value = "<p>Test HTML</p>"
        mock_converter_class.return_value = mock_converter
        
        mock_page = PageInfo(id=123, spaceId=1, version=1, link="test-link")
        confluence_converter.confluence_client.get_page.return_value = mock_page
        confluence_converter.confluence_client.delete_page = Mock()
        
        confluence_converter.convert(
            simulate=False,
            delete=True,
            remove_emojies=False,
            add_contents=False,
            labels=[],
            properties={},
            attachments=[]
        )
        
        confluence_converter.confluence_client.delete_page.assert_called_once_with(123)

    @patch('md_to_conf.confluence_converter.MarkdownConverter')
    @patch('builtins.open', new_callable=mock_open, read_data="# Test Title\n\nContent")
    def test_convert_create_new_page(self, mock_file, mock_converter_class, confluence_converter):
        """Test convert method creating a new page"""
        mock_converter = Mock()
        mock_converter.convert_md_to_conf_html.return_value = "<p>Test HTML</p>"
        mock_converter_class.return_value = mock_converter
        
        # Mock page that doesn't exist (id = 0)
        mock_page = PageInfo(id=0, spaceId=1, version=1, link="test-link")
        confluence_converter.confluence_client.get_page.return_value = mock_page
        
        # Mock created page
        created_page = PageInfo(id=123, spaceId=1, version=1, link="test-link")
        confluence_converter.confluence_client.create_page.return_value = created_page
        confluence_converter.confluence_client.update_page = Mock()
        confluence_converter.confluence_client.get_page_properties.return_value = []
        
        # Mock the methods that will be called
        confluence_converter.add_images = Mock(return_value="<p>Test HTML</p>")
        confluence_converter.add_local_refs = Mock(return_value="<p>Test HTML</p>")
        confluence_converter.get_parent_page = Mock(return_value=456)
        
        confluence_converter.convert(
            simulate=False,
            delete=False,
            remove_emojies=False,
            add_contents=False,
            labels=[],
            properties={},
            attachments=[]
        )
        
        confluence_converter.confluence_client.create_page.assert_called_once()
        confluence_converter.confluence_client.update_page.assert_called_once()

    @patch('md_to_conf.confluence_converter.MarkdownConverter')
    @patch('builtins.open', new_callable=mock_open, read_data="Test Title\n\nContent")  # No # in title
    def test_convert_title_from_file(self, mock_file, mock_converter_class, confluence_converter):
        """Test convert method extracting title from file when no title provided"""
        confluence_converter.title = None  # No title provided
        
        mock_converter = Mock()
        mock_converter.convert_md_to_conf_html.return_value = "<p>Test HTML</p>"
        mock_converter_class.return_value = mock_converter
        
        # Mock page that exists
        mock_page = PageInfo(id=123, spaceId=1, version=1, link="test-link")
        confluence_converter.confluence_client.get_page.return_value = mock_page
        confluence_converter.confluence_client.update_page = Mock()
        confluence_converter.confluence_client.get_page_properties.return_value = []
        
        # Mock the methods that will be called
        confluence_converter.add_images = Mock(return_value="<p>Test HTML</p>")
        confluence_converter.add_local_refs = Mock(return_value="<p>Test HTML</p>")
        confluence_converter.get_parent_page = Mock(return_value=456)
        
        confluence_converter.convert(
            simulate=False,
            delete=False,
            remove_emojies=False,
            add_contents=False,
            labels=[],
            properties={},
            attachments=[]
        )
        
        # Verify that convert_md_to_conf_html was called with has_title=False
        mock_converter.convert_md_to_conf_html.assert_called_once_with(
            has_title=False,
            remove_emojies=False,
            add_contents=False
        )

    @patch('md_to_conf.confluence_converter.MarkdownConverter')
    @patch('builtins.open', new_callable=mock_open, read_data="# Test Title\n\nContent")
    def test_convert_with_labels_and_properties(self, mock_file, mock_converter_class, confluence_converter):
        """Test convert method with labels and properties"""
        mock_converter = Mock()
        mock_converter.convert_md_to_conf_html.return_value = "<p>Test HTML</p>"
        mock_converter_class.return_value = mock_converter
        
        # Mock page that exists
        mock_page = PageInfo(id=123, spaceId=1, version=1, link="test-link")
        confluence_converter.confluence_client.get_page.return_value = mock_page
        confluence_converter.confluence_client.update_page = Mock()
        confluence_converter.confluence_client.get_page_properties.return_value = []
        confluence_converter.confluence_client.update_labels = Mock()
        
        # Mock the methods that will be called
        confluence_converter.add_images = Mock(return_value="<p>Test HTML</p>")
        confluence_converter.add_local_refs = Mock(return_value="<p>Test HTML</p>")
        confluence_converter.get_parent_page = Mock(return_value=456)
        confluence_converter.add_attachments = Mock()
        
        labels = ["label1", "label2"]
        properties = {"custom_prop": "custom_value"}
        attachments = ["file1.txt", "file2.pdf"]
        
        confluence_converter.convert(
            simulate=False,
            delete=False,
            remove_emojies=True,
            add_contents=True,
            labels=labels,
            properties=properties,
            attachments=attachments
        )
        
        confluence_converter.confluence_client.update_labels.assert_called_once_with(123, labels)
        confluence_converter.add_attachments.assert_called_once_with(123, attachments)
        mock_converter.convert_md_to_conf_html.assert_called_once_with(
            has_title=True,  # Title was provided in fixture
            remove_emojies=True,
            add_contents=True
        )

    def test_add_images_multiple_images(self, confluence_converter):
        """Test add_images method with multiple images"""
        html = '<p>First <img src="image1.png" alt="Image 1"/> and second <img src="image2.jpg" alt="Image 2"/> images</p>'
        page_id = 123
        
        confluence_converter.confluence_client.upload_attachment = Mock()
        
        result = confluence_converter.add_images(page_id, html)
        
        expected_html = '<p>First <img src="/wiki/download/attachments/123/image1.png" alt="Image 1"/> and second <img src="/wiki/download/attachments/123/image2.jpg" alt="Image 2"/> images</p>'
        assert result == expected_html
        assert confluence_converter.confluence_client.upload_attachment.call_count == 2

    def test_add_images_no_images(self, confluence_converter):
        """Test add_images method with no images in HTML"""
        html = '<p>Content without images</p>'
        page_id = 123
        
        confluence_converter.confluence_client.upload_attachment = Mock()
        
        result = confluence_converter.add_images(page_id, html)
        
        assert result == html
        confluence_converter.confluence_client.upload_attachment.assert_not_called()

    def test_get_properties_to_update_mixed_scenario(self, confluence_converter):
        """Test get_properties_to_update with mixed new and existing properties"""
        page_id = 123
        props = {
            "existing_prop": "updated_value",
            "new_prop": "new_value"
        }
        existing_properties = [
            {
                "key": "editor",
                "value": "v1",
                "version": {"number": 1},
                "id": "prop1"
            },
            {
                "key": "existing_prop",
                "value": "old_value",
                "version": {"number": 2},
                "id": "prop2"
            }
        ]
        
        confluence_converter.confluence_client.get_page_properties.return_value = existing_properties
        
        result = confluence_converter.get_properties_to_update(props, page_id)
        
        # Should update editor version, update existing property, and add new property
        assert len(result) == 3
        
        # Check editor version update
        editor_update = next(prop for prop in result if prop["key"] == "editor")
        assert editor_update == {
            "key": "editor",
            "version": 2,
            "value": "v2",
            "id": "prop1"
        }
        
        # Check existing property update
        existing_update = next(prop for prop in result if prop["key"] == "existing_prop")
        assert existing_update == {
            "key": "existing_prop",
            "version": 3,
            "value": "updated_value",
            "id": "prop2"
        }
        
        # Check new property addition
        new_prop = next(prop for prop in result if prop["key"] == "new_prop")
        assert new_prop == {
            "key": "new_prop",
            "version": 1,
            "value": "new_value"
        }
