import pytest
from md_to_conf import MarkdownConverter


URL = "https://domain.confluence.net/wiki"


@pytest.fixture
def test_converter_basic() -> MarkdownConverter:
    return MarkdownConverter("tests/testfiles/basic.md", URL, "default", 2)


@pytest.fixture
def test_converter_advanced() -> MarkdownConverter:
    return MarkdownConverter("tests/testfiles/advanced.md", URL, "default", 2)


@pytest.fixture
def test_converter_github_alerts() -> MarkdownConverter:
    return MarkdownConverter("tests/testfiles/github-alerts.md", URL, "default", 2)


def test_converter_init():
    md_file = "tests/testfiles/basic.md"
    url = "https://domain.confluence.net/wiki"
    md_source = "default"
    editor_version = 2

    converter = MarkdownConverter(md_file, url, md_source, editor_version)

    assert converter.md_file == md_file
    assert converter.api_url == url
    assert converter.md_source == md_source
    assert converter.editor_version == editor_version


def test_converter_basic_test(test_converter_basic: MarkdownConverter, snapshot):
    html = test_converter_basic.get_html_from_markdown()
    assert html == snapshot


def test_converter_html(test_converter_basic: MarkdownConverter, snapshot):
    html = test_converter_basic.convert_md_to_conf_html(
        has_title=False, remove_emojies=False, add_contents=False
    )
    assert html == snapshot


def test_converter_html_advanced_with_toc(
    test_converter_advanced: MarkdownConverter, snapshot
):
    html = test_converter_advanced.convert_md_to_conf_html(
        has_title=False, remove_emojies=True, add_contents=True
    )
    assert html == snapshot


def test_converter_html_advanced(test_converter_advanced: MarkdownConverter, snapshot):
    html = test_converter_advanced.convert_md_to_conf_html(
        has_title=False, remove_emojies=True, add_contents=False
    )
    assert html == snapshot


def test_slug(test_converter_basic: MarkdownConverter):
    slug = test_converter_basic.slug("<tag>The $slug</tag>", False)
    assert slug == "The-slug"


def test_slug_lower(test_converter_basic: MarkdownConverter):
    slug = test_converter_basic.slug("<tag>The $slug</tag>", True)
    assert slug == "the-slug"


def test_convert_comment_block(test_converter_basic: MarkdownConverter):
    slug = test_converter_basic.convert_comment_block("<!-- some comments go here -->")
    assert slug == "<ac:placeholder> some comments go here </ac:placeholder>"


def test_toc_convert(test_converter_basic: MarkdownConverter, snapshot):
    slug = test_converter_basic.create_table_of_content(
        "<h1>First heading</h1> <p>[TOC]</p> <h2>Second heading</h2>"
    )

    assert slug == snapshot


def test_process_links_editor_v1():
    """Test process_links function with editor version 1"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 1)

    html = ('<p>See <a href="#section-1">Section 1</a> and '
            '<a href="#section-2">Section 2</a> for details</p>')
    links = ['<a href="#section-1">Section 1</a>', '<a href="#section-2">Section 2</a>']
    headers_map = {"#section-1": "Section1", "#section-2": "Section2"}
    space_key = "TEST"
    page_id = 12345
    title = "Test Page"

    result = converter.process_links(
        html, links, headers_map, space_key, page_id, title
    )

    expected_replacement1 = (
        '<ac:link ac:anchor="Section1">'
        "<ac:plain-text-link-body>"
        "<![CDATA[Section 1]]></ac:plain-text-link-body></ac:link>"
    )
    expected_replacement2 = (
        '<ac:link ac:anchor="Section2">'
        "<ac:plain-text-link-body>"
        "<![CDATA[Section 2]]></ac:plain-text-link-body></ac:link>"
    )

    assert expected_replacement1 in result
    assert expected_replacement2 in result


def test_process_links_editor_v2():
    """Test process_links function with editor version 2"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = ('<p>See <a href="#section-1">Section 1</a> and '
            '<a href="#section-2">Section 2</a> for details</p>')
    links = ['<a href="#section-1">Section 1</a>', '<a href="#section-2">Section 2</a>']
    headers_map = {"#section-1": "Section-1", "#section-2": "Section-2"}
    space_key = "TEST"
    page_id = 12345
    title = "Test Page"

    result = converter.process_links(html, links, headers_map, space_key, page_id, title)

    expected_replacement1 = ('<a href="https://example.com/wiki/spaces/TEST/pages/12345/'
                             'Test+Page#Section-1" title="Section 1">Section 1</a>')
    expected_replacement2 = ('<a href="https://example.com/wiki/spaces/TEST/pages/12345/'
                             'Test+Page#Section-2" title="Section 2">Section 2</a>')
    links = ['<a href="#section-1">Section 1</a>', '<a href="#section-2">Section 2</a>']
    headers_map = {"#section-1": "Section-1", "#section-2": "Section-2"}
    space_key = "TEST"
    page_id = 12345
    title = "Test Page"

    result = converter.process_links(
        html, links, headers_map, space_key, page_id, title
    )

    expected_replacement1 = '<a href="https://example.com/wiki/spaces/TEST/pages/12345/Test+Page#Section-1" title="Section 1">Section 1</a>'
    expected_replacement2 = '<a href="https://example.com/wiki/spaces/TEST/pages/12345/Test+Page#Section-2" title="Section 2">Section 2</a>'

    assert expected_replacement1 in result
    assert expected_replacement2 in result


def test_process_links_with_title_spaces():
    """Test process_links function with title containing spaces"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = '<p>See <a href="#section-1">Section 1</a> for details</p>'
    links = ['<a href="#section-1">Section 1</a>']
    headers_map = {"#section-1": "Section-1"}
    space_key = "TEST"
    page_id = 12345
    title = "Test Page With Spaces"

    result = converter.process_links(
        html, links, headers_map, space_key, page_id, title
    )

    expected_replacement = ('<a href="https://example.com/wiki/spaces/TEST/pages/12345/'
                             'Test+Page+With+Spaces#Section-1" title="Section 1">Section 1</a>')
    assert expected_replacement in result


def test_process_links_with_html_tags_in_alt_text_v1():
    """Test process_links function with HTML tags in alt text for editor v1"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 1)

    html = (
        '<p>See <a href="#section-1"><strong>Bold</strong> Section</a> for details</p>'
    )
    links = ['<a href="#section-1"><strong>Bold</strong> Section</a>']
    headers_map = {"#section-1": "Section1"}
    space_key = "TEST"
    page_id = 12345
    title = "Test Page"

    result = converter.process_links(
        html, links, headers_map, space_key, page_id, title
    )

    # HTML tags should be stripped from alt text in editor v1
    expected_replacement = (
        '<ac:link ac:anchor="Section1">'
        "<ac:plain-text-link-body>"
        "<![CDATA[ Section]]></ac:plain-text-link-body></ac:link>"
    )

    assert expected_replacement in result


def test_process_links_with_html_tags_in_alt_text_v2():
    """Test process_links function with HTML tags in alt text for editor v2"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = (
        '<p>See <a href="#section-1"><strong>Bold</strong> Section</a> for details</p>'
    )
    links = ['<a href="#section-1"><strong>Bold</strong> Section</a>']
    headers_map = {"#section-1": "Section-1"}
    space_key = "TEST"
    page_id = 12345
    title = "Test Page"

    result = converter.process_links(
        html, links, headers_map, space_key, page_id, title
    )

    # HTML tags should be preserved in alt text for editor v2
    expected_replacement = '<a href="https://example.com/wiki/spaces/TEST/pages/12345/Test+Page#Section-1" title="<strong>Bold</strong> Section"><strong>Bold</strong> Section</a>'

    assert expected_replacement in result


def test_process_links_header_not_in_map():
    """Test process_links function when header reference is not in headers_map"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = '<p>Some content</p><a href="#nonexistent">Missing Link</a>'
    links = ['<a href="#nonexistent">Missing Link</a>']
    headers_map = {"#section-1": "Section-1"}  # Different key
    space_key = "TEST"
    page_id = 12345
    title = "Test Page"

    result = converter.process_links(
        html, links, headers_map, space_key, page_id, title
    )

    # Original link should remain unchanged when not found in headers_map
    assert '<a href="#nonexistent">Missing Link</a>' in result


def test_process_links_empty_links_list():
    """Test process_links function with empty links list"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<p>Some content without links</p>"
    links = []
    headers_map = {"#section-1": "Section-1"}
    space_key = "TEST"
    page_id = 12345
    title = "Test Page"

    result = converter.process_links(
        html, links, headers_map, space_key, page_id, title
    )

    # HTML should remain unchanged when no links provided
    assert result == html


def test_process_links_multiple_same_links():
    """Test process_links function with multiple instances of the same link"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = '<p>First <a href="#section-1">Section 1</a> and second <a href="#section-1">Section 1</a></p>'
    links = ['<a href="#section-1">Section 1</a>']  # Only one unique link
    headers_map = {"#section-1": "Section-1"}
    space_key = "TEST"
    page_id = 12345
    title = "Test Page"

    result = converter.process_links(
        html, links, headers_map, space_key, page_id, title
    )

    expected_replacement = '<a href="https://example.com/wiki/spaces/TEST/pages/12345/Test+Page#Section-1" title="Section 1">Section 1</a>'

    # Both instances should be replaced
    assert result.count(expected_replacement) == 2
    assert '<a href="#section-1">Section 1</a>' not in result


def test_process_links_complex_anchor_refs():
    """Test process_links function with complex anchor references"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = '<p>See <a href="#complex-section-with-numbers-123">Complex Section</a> for details</p>'
    links = ['<a href="#complex-section-with-numbers-123">Complex Section</a>']
    headers_map = {
        "#complex-section-with-numbers-123": "Complex-Section-With-Numbers-123"
    }
    space_key = "COMPLEX"
    page_id = 98765
    title = "Complex Test Page"

    result = converter.process_links(
        html, links, headers_map, space_key, page_id, title
    )

    expected_replacement = '<a href="https://example.com/wiki/spaces/COMPLEX/pages/98765/Complex+Test+Page#Complex-Section-With-Numbers-123" title="Complex Section">Complex Section</a>'

    assert expected_replacement in result


def test_process_headers_editor_v1_basic():
    """Test process_headers function with editor version 1 basic functionality"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 1)

    headers = ["Section 1", "Section 2", "Another Section"]
    ref_prefix = "#"
    ref_postfix = ".%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    expected = {
        "#section-1": "Section1",
        "#section-2": "Section2",
        "#another-section": "AnotherSection",
    }

    assert result == expected


def test_process_headers_editor_v2_basic():
    """Test process_headers function with editor version 2 basic functionality"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    headers = ["Section 1", "Section 2", "Another Section"]
    ref_prefix = "#"
    ref_postfix = ".%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    expected = {
        "#section-1": "Section-1",
        "#section-2": "Section-2",
        "#another-section": "Another-Section",
    }

    assert result == expected


def test_process_headers_with_html_tags_v1():
    """Test process_headers function with HTML tags in headers for editor v1"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 1)

    headers = [
        "<strong>Bold</strong> Section",
        "<em>Italic</em> Text",
        "<code>Code</code> Block",
    ]
    ref_prefix = "#"
    ref_postfix = ".%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    expected = {
        "#bold-section": "Section",
        "#italic-text": "Text",
        "#code-block": "Block",
    }

    assert result == expected


def test_process_headers_with_html_tags_v2():
    """Test process_headers function with HTML tags in headers for editor v2"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    headers = [
        "<strong>Bold</strong> Section",
        "<em>Italic</em> Text",
        "<code>Code</code> Block",
    ]
    ref_prefix = "#"
    ref_postfix = ".%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    expected = {
        "#bold-section": "Bold-Section",
        "#italic-text": "Italic-Text",
        "#code-block": "Code-Block",
    }

    assert result == expected


def test_process_headers_with_duplicate_headers_v1():
    """Test process_headers function with duplicate headers for editor v1"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 1)

    headers = ["Section 1", "Section 1", "Section 1"]
    ref_prefix = "#"
    ref_postfix = ".%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    expected = {
        "#section-1": "Section1",
        "#section-1.1": "Section1.1",
        "#section-1.2": "Section1.2",
    }

    assert result == expected


def test_process_headers_with_duplicate_headers_v2():
    """Test process_headers function with duplicate headers for editor v2"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    headers = ["Section 1", "Section 1", "Section 1"]
    ref_prefix = "#"
    ref_postfix = ".%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    expected = {
        "#section-1": "Section-1",
        "#section-1.1": "Section-1.1",
        "#section-1.2": "Section-1.2",
    }

    assert result == expected


def test_process_headers_with_special_characters():
    """Test process_headers function with special characters in headers"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    headers = ["Section #1", "Section @2", "Section $3!", "Section & More"]
    ref_prefix = "#"
    ref_postfix = ".%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    expected = {
        "#section-1": "Section-1",
        "#section-2": "Section-2",
        "#section-3": "Section-3",
        "#section--more": "Section--More",
    }

    assert result == expected


def test_process_headers_with_numbers_and_mixed_case():
    """Test process_headers function with numbers and mixed case"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    headers = ["API Version 2.0", "HTTPs Protocol", "JSONParser Class"]
    ref_prefix = "#"
    ref_postfix = ".%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    expected = {
        "#api-version-20": "API-Version-20",
        "#https-protocol": "HTTPs-Protocol",
        "#jsonparser-class": "JSONParser-Class",
    }

    assert result == expected


def test_process_headers_with_empty_headers():
    """Test process_headers function with empty headers list"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    headers = []
    ref_prefix = "#"
    ref_postfix = ".%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    assert result == {}


def test_process_headers_with_spaces_only_v1():
    """Test process_headers function with headers containing only spaces for editor v1"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 1)

    headers = ["  Multiple   Spaces  ", "Tab\tCharacters", "Newline\nCharacter"]
    ref_prefix = "#"
    ref_postfix = ".%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    expected = {
        "#--multiple---spaces--": "MultipleSpaces",
        "#tabcharacters": "Tab\tCharacters",
        "#newlinecharacter": "Newline\nCharacter",
    }

    assert result == expected


def test_process_headers_with_custom_prefix_postfix():
    """Test process_headers function with custom prefix and postfix"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    headers = ["Section A", "Section A", "Section B"]
    ref_prefix = "custom-"
    ref_postfix = "-v%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    expected = {
        "custom-section-a": "Section-A",
        "custom-section-a-v1": "Section-A.1",
        "custom-section-b": "Section-B",
    }

    assert result == expected


def test_process_headers_unicode_characters():
    """Test process_headers function with unicode characters"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    headers = ["Café Section", "Naïve Approach", "Résumé Overview"]
    ref_prefix = "#"
    ref_postfix = ".%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    expected = {
        "#caf-section": "Caf-Section",
        "#nave-approach": "Nave-Approach",
        "#rsum-overview": "Rsum-Overview",
    }

    assert result == expected


def test_process_headers_complex_html_structure_v1():
    """Test process_headers function with complex HTML structure for editor v1"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 1)

    headers = [
        "<h1><strong>Main</strong> <em>Title</em></h1>",
        "<span class='highlight'>Important</span> Section",
        "<a href='#'>Linked</a> Header",
    ]
    ref_prefix = "#"
    ref_postfix = ".%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    expected = {
        "#main-title": "",
        "#important-section": "Section",
        "#linked-header": "Header",
    }

    assert result == expected


def test_process_headers_complex_html_structure_v2():
    """Test process_headers function with complex HTML structure for editor v2"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    headers = [
        "<h1><strong>Main</strong> <em>Title</em></h1>",
        "<span class='highlight'>Important</span> Section",
        "<a href='#'>Linked</a> Header",
    ]
    ref_prefix = "#"
    ref_postfix = ".%s"

    result = converter.process_headers(ref_prefix, ref_postfix, headers)

    expected = {
        "#main-title": "Main-Title",
        "#important-section": "Important-Section",
        "#linked-header": "Linked-Header",
    }

    assert result == expected


def test_convert_github_alerts_note():
    """Test conversion of GitHub NOTE alert to Confluence info macro"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<blockquote><p>[!NOTE] This is a note alert with important information.</p></blockquote>"

    result = converter.convert_github_alerts(html)

    expected = '<p><ac:structured-macro ac:name="info"><ac:rich-text-body><p>This is a note alert with important information.</p></ac:rich-text-body></ac:structured-macro></p>'

    assert result == expected


def test_convert_github_alerts_tip():
    """Test conversion of GitHub TIP alert to Confluence tip macro"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<blockquote><p>[!TIP] Here is a helpful tip for users.</p></blockquote>"

    result = converter.convert_github_alerts(html)

    expected = '<p><ac:structured-macro ac:name="tip"><ac:rich-text-body><p>Here is a helpful tip for users.</p></ac:rich-text-body></ac:structured-macro></p>'

    assert result == expected


def test_convert_github_alerts_important():
    """Test conversion of GitHub IMPORTANT alert to Confluence ADF panel"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<blockquote><p>[!IMPORTANT] This is critical information users must know.</p></blockquote>"

    result = converter.convert_github_alerts(html)

    expected = '<ac:adf-extension><ac:adf-node type="panel"><ac:adf-attribute key="panel-type">note</ac:adf-attribute><ac:adf-content><p>This is critical information users must know.</p></ac:adf-content></ac:adf-node></ac:adf-extension>'

    assert result == expected


def test_convert_github_alerts_warning():
    """Test conversion of GitHub WARNING alert to Confluence note macro"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<blockquote><p>[!WARNING] This is a warning about potential issues.</p></blockquote>"

    result = converter.convert_github_alerts(html)

    expected = '<p><ac:structured-macro ac:name="note"><ac:rich-text-body><p>This is a warning about potential issues.</p></ac:rich-text-body></ac:structured-macro></p>'

    assert result == expected


def test_convert_github_alerts_caution():
    """Test conversion of GitHub CAUTION alert to Confluence warning macro"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<blockquote><p>[!CAUTION] Be very careful when performing this action.</p></blockquote>"

    result = converter.convert_github_alerts(html)

    expected = '<p><ac:structured-macro ac:name="warning"><ac:rich-text-body><p>Be very careful when performing this action.</p></ac:rich-text-body></ac:structured-macro></p>'

    assert result == expected


def test_convert_github_alerts_case_insensitive():
    """Test that GitHub alerts work with different cases"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<blockquote><p>[!note] This should work with lowercase.</p></blockquote>"

    result = converter.convert_github_alerts(html)

    expected = '<p><ac:structured-macro ac:name="info"><ac:rich-text-body><p>This should work with lowercase.</p></ac:rich-text-body></ac:structured-macro></p>'

    assert result == expected


def test_convert_github_alerts_multiline():
    """Test GitHub alerts with multiline content"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<blockquote><p>[!NOTE] This is a note with multiple lines</p><p>Second paragraph of the note</p></blockquote>"

    result = converter.convert_github_alerts(html)

    expected = '<p><ac:structured-macro ac:name="info"><ac:rich-text-body><p>This is a note with multiple lines</p><p>Second paragraph of the note</p></ac:rich-text-body></ac:structured-macro></p>'

    assert result == expected


def test_convert_github_alerts_with_formatting():
    """Test GitHub alerts with HTML formatting inside"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<blockquote><p>[!TIP] This tip has <strong>bold</strong> and <em>italic</em> text.</p></blockquote>"

    result = converter.convert_github_alerts(html)

    expected = '<p><ac:structured-macro ac:name="tip"><ac:rich-text-body><p>This tip has <strong>bold</strong> and <em>italic</em> text.</p></ac:rich-text-body></ac:structured-macro></p>'

    assert result == expected


def test_convert_github_alerts_no_alert():
    """Test that regular blockquotes are not affected by GitHub alert conversion"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<blockquote><p>This is just a regular blockquote without any alert syntax.</p></blockquote>"

    result = converter.convert_github_alerts(html)

    # Should remain unchanged
    assert result == html


def test_convert_github_alerts_unknown_type():
    """Test that unknown alert types are ignored"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<blockquote><p>[!UNKNOWN] This alert type does not exist.</p></blockquote>"

    result = converter.convert_github_alerts(html)

    # Should remain unchanged
    assert result == html


def test_convert_info_macros_github_precedence():
    """Test that GitHub alerts take precedence over other blockquote conversions"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    # Test input with both GitHub alert and traditional format
    html = "<blockquote><p>[!NOTE] GitHub alert</p></blockquote><blockquote><p>Note: Traditional note</p></blockquote>"

    result = converter.convert_info_macros(html)

    # GitHub alert should be converted, traditional should be handled by existing logic
    assert '<ac:structured-macro ac:name="info">' in result
    assert "GitHub alert" in result


def test_convert_github_alerts_empty_content():
    """Test GitHub alerts with minimal content"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<blockquote><p>[!NOTE]</p></blockquote>"

    result = converter.convert_github_alerts(html)

    expected = '<p><ac:structured-macro ac:name="info"><ac:rich-text-body><p></p></ac:rich-text-body></ac:structured-macro></p>'

    assert result == expected


def test_github_alerts_integration_example():
    """Integration test showing GitHub alerts in action"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    # Example markdown converted to HTML that might come from the markdown parser
    html = """<h1>Documentation Example</h1>
<blockquote><p>[!NOTE] This feature requires Python 3.8 or later.</p></blockquote>
<blockquote><p>[!TIP] Use virtual environments for better dependency management.</p></blockquote>
<blockquote><p>[!WARNING] Make sure to backup your data before proceeding.</p></blockquote>
<blockquote><p>[!CAUTION] This operation cannot be undone.</p></blockquote>"""

    result = converter.convert_info_macros(html)

    # Verify all alert types are converted
    assert 'ac:structured-macro ac:name="info"' in result  # NOTE
    assert 'ac:structured-macro ac:name="tip"' in result  # TIP
    assert 'ac:structured-macro ac:name="note"' in result  # WARNING
    assert 'ac:structured-macro ac:name="warning"' in result  # CAUTION

    # Verify the content is preserved
    assert "Python 3.8 or later" in result
    assert "virtual environments" in result
    assert "backup your data" in result
    assert "cannot be undone" in result


def test_convert_github_alerts_redos_resistance():
    """Test that GitHub alerts processing is resistant to ReDoS attacks"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    # Create a potentially malicious input that could cause ReDoS with vulnerable regex
    # This creates deeply nested structure that would cause catastrophic backtracking
    malicious_content = "<p>" + "a" * 1000 + "</p>" * 100
    html = f"<blockquote><p>[!NOTE] Content</p>{malicious_content}</blockquote>"

    # This should complete quickly without hanging
    import time

    start_time = time.time()
    result = converter.convert_github_alerts(html)
    end_time = time.time()

    # Should complete in well under a second
    assert end_time - start_time < 1.0

    # Should still process the alert correctly
    assert 'ac:structured-macro ac:name="info"' in result
    assert "Content" in result


def test_convert_github_alerts_malformed_html_resistance():
    """Test that GitHub alerts processing handles malformed HTML gracefully"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    # Test with unclosed tags and weird structures
    malformed_cases = [
        "<blockquote><p>[!NOTE] Content without closing p</blockquote>",
        "<blockquote><p>[!TIP] Content<p>nested p</p></blockquote>",
        "<blockquote><p>[!WARNING] Content</p><broken>tag</blockquote>",
        "<blockquote><p>[!NOTE]</p></blockquote>",  # Empty content
    ]

    for malformed_html in malformed_cases:
        # Should not raise exceptions
        try:
            result = converter.convert_github_alerts(malformed_html)
            # Should either convert or leave unchanged, but not crash
            assert isinstance(result, str)
        except Exception as e:
            pytest.fail(
                f"convert_github_alerts raised {type(e).__name__}: {e} for input: {malformed_html}"
            )


def test_parse_github_alert_valid_cases():
    """Test the _parse_github_alert method with valid inputs"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    # Test valid NOTE alert
    quote = "<p>[!NOTE] This is a note content</p><p>Additional content</p>"
    result = converter._parse_github_alert(quote)

    assert result is not None
    assert result["alert_type"] == "NOTE"
    assert result["first_line_content"] == "This is a note content"
    assert result["remaining_content"] == "<p>Additional content</p>"


def test_parse_github_alert_case_insensitive():
    """Test that _parse_github_alert handles case insensitive alert types"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    quote = "<p>[!tip] This is a tip in lowercase</p>"
    result = converter._parse_github_alert(quote)

    assert result is not None
    assert result["alert_type"] == "TIP"
    assert result["first_line_content"] == "This is a tip in lowercase"


def test_parse_github_alert_invalid_cases():
    """Test the _parse_github_alert method with invalid inputs"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    invalid_cases = [
        "<p>Regular blockquote content</p>",  # No alert syntax
        "<p>[!INVALID] Unknown alert type</p>",  # Unknown alert type
        "<p>[!NOTE] Content without closing p",  # Malformed HTML
        "",  # Empty string
        "<p>[NOTE] Missing exclamation</p>",  # Missing !
    ]

    for invalid_quote in invalid_cases:
        result = converter._parse_github_alert(invalid_quote)
        assert result is None, f"Expected None for input: {invalid_quote}"


def test_get_alert_macro_tags():
    """Test the _get_alert_macro_tags method"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    # Test valid alert types
    note_tags = converter._get_alert_macro_tags("NOTE")
    assert note_tags is not None
    assert 'ac:name="info"' in note_tags[0]

    tip_tags = converter._get_alert_macro_tags("TIP")
    assert tip_tags is not None
    assert 'ac:name="tip"' in tip_tags[0]

    important_tags = converter._get_alert_macro_tags("IMPORTANT")
    assert important_tags is not None
    assert "ac:adf-extension" in important_tags[0]
    assert "panel-type" in important_tags[0]

    warning_tags = converter._get_alert_macro_tags("WARNING")
    assert warning_tags is not None
    assert 'ac:name="note"' in warning_tags[0]

    caution_tags = converter._get_alert_macro_tags("CAUTION")
    assert caution_tags is not None
    assert 'ac:name="warning"' in caution_tags[0]

    # Test invalid alert type
    invalid_tags = converter._get_alert_macro_tags("INVALID")
    assert invalid_tags is None


def test_build_alert_content():
    """Test the _build_alert_content method"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    # Test with both first line and remaining content
    result = converter._build_alert_content("First line", "<p>Second paragraph</p>")
    assert result == "<p>First line</p><p>Second paragraph</p>"

    # Test with only first line content
    result = converter._build_alert_content("Only first line", "")
    assert result == "<p>Only first line</p>"

    # Test with only remaining content
    result = converter._build_alert_content("", "<p>Only remaining</p>")
    assert result == "<p>Only remaining</p>"

    # Test with no content
    result = converter._build_alert_content("", "")
    assert result == "<p></p>"


def test_create_alert_macro():
    """Test the _create_alert_macro method"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    # Test valid alert info
    alert_info = {
        "alert_type": "NOTE",
        "first_line_content": "Test content",
        "remaining_content": "",
    }

    result = converter._create_alert_macro(alert_info)
    assert result is not None
    assert 'ac:name="info"' in result
    assert "Test content" in result
    assert "</ac:structured-macro>" in result

    # Test IMPORTANT alert (special ADF format)
    alert_info["alert_type"] = "IMPORTANT"
    result = converter._create_alert_macro(alert_info)
    assert result is not None
    assert "ac:adf-extension" in result
    assert "panel-type" in result

    # Test invalid alert type
    alert_info["alert_type"] = "INVALID"
    result = converter._create_alert_macro(alert_info)
    assert result is None


def test_type_annotations_unknown_alert_integration():
    """Test that unknown alert types are handled gracefully with proper type annotations"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    # Test complete flow with unknown alert type
    html = (
        "<blockquote><p>[!UNKNOWN] This should be ignored completely</p></blockquote>"
    )
    result = converter.convert_github_alerts(html)

    # Should remain unchanged since unknown alert types return None from _create_alert_macro
    assert result == html

    # Test that valid alert types still work
    html_valid = "<blockquote><p>[!NOTE] This should be converted</p></blockquote>"
    result_valid = converter.convert_github_alerts(html_valid)

    # Should be converted
    assert result_valid != html_valid
    assert 'ac:name="info"' in result_valid


def test_optional_return_types():
    """Test that methods with Optional return types handle None correctly"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    # Test _parse_github_alert returns None for invalid input
    result = converter._parse_github_alert("<p>Not an alert</p>")
    assert result is None

    # Test _get_alert_macro_tags returns None for unknown type
    result = converter._get_alert_macro_tags("UNKNOWN")
    assert result is None

    # Test _create_alert_macro returns None for invalid alert type
    invalid_alert = {
        "alert_type": "UNKNOWN",
        "first_line_content": "content",
        "remaining_content": "",
    }
    result = converter._create_alert_macro(invalid_alert)
    assert result is None


def test_process_refs_basic_footnote():
    """Test basic footnote processing with single footnote"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = '<p>This text has a footnote[^1].</p>\n[^1]: This is footnote definition with <a href="http://example.com">link</a>.'

    result = converter.process_refs(html)

    # Should convert [^1] to superscript link and remove footnote definition
    assert '<a id="test" href="http://example.com"><sup>1</sup></a>' in result
    assert "This text has a footnote" in result
    assert "[^1]: This is footnote definition" not in result


def test_process_refs_multiple_footnotes():
    """Test footnote processing with multiple footnotes"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = """<p>First footnote[^1] and second footnote[^2].</p>
[^1]: First footnote with <a href="http://example1.com">link1</a>.
[^2]: Second footnote with <a href="http://example2.com">link2</a>."""

    result = converter.process_refs(html)

    # Should convert both footnotes
    assert '<a id="test" href="http://example1.com"><sup>1</sup></a>' in result
    assert '<a id="test" href="http://example2.com"><sup>2</sup></a>' in result
    assert "First footnote[^1]" not in result
    assert "second footnote[^2]" not in result
    assert "[^1]: First footnote" not in result
    assert "[^2]: Second footnote" not in result


def test_process_refs_footnote_in_paragraph_tags():
    """Test footnote processing when footnote definition is wrapped in paragraph tags"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = '<p>Text with footnote[^1].</p><p>[^1]: Definition with <a href="http://example.com">link</a>.</p>'

    result = converter.process_refs(html)

    # Should handle footnote definition in paragraph tags
    assert '<a id="test" href="http://example.com"><sup>1</sup></a>' in result
    assert "Text with footnote" in result
    assert "[^1]: Definition" not in result


def test_process_refs_mixed_paragraph_and_newline_footnotes():
    """Test footnote processing with mixed format footnote definitions"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = """<p>Text with footnote[^1] and another[^2].</p>
[^1]: Newline footnote with <a href="http://example1.com">link1</a>.
<p>[^2]: Paragraph footnote with <a href="http://example2.com">link2</a>.</p>"""

    result = converter.process_refs(html)

    # Should handle both formats
    assert '<a id="test" href="http://example1.com"><sup>1</sup></a>' in result
    assert '<a id="test" href="http://example2.com"><sup>2</sup></a>' in result
    assert "[^1]: Newline footnote" not in result
    assert "[^2]: Paragraph footnote" not in result


def test_process_refs_footnote_with_complex_link():
    """Test footnote processing with complex link attributes"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = """<p>Text with footnote[^1].</p>
[^1]: Complex footnote with <a href="http://example.com?param=value&amp;other=test" title="Example Link" target="_blank">complex link</a>."""

    result = converter.process_refs(html)

    # Should extract href correctly from complex link
    assert (
        '<a id="test" href="http://example.com?param=value&amp;other=test"><sup>1</sup></a>'
        in result
    )
    assert "[^1]: Complex footnote" not in result


def test_process_refs_footnote_with_multiple_links():
    """Test footnote processing when footnote definition has multiple links"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = """<p>Text with footnote[^1].</p>
[^1]: Footnote with <a href="http://first.com">first link</a> and <a href="http://second.com">second link</a>."""

    result = converter.process_refs(html)

    # Should use the first href found
    assert '<a id="test" href="http://first.com"><sup>1</sup></a>' in result
    assert "[^1]: Footnote with" not in result


def test_process_refs_no_footnotes():
    """Test process_refs when there are no footnotes in the HTML"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<p>This is just regular text without any footnotes.</p>"

    result = converter.process_refs(html)

    # Should return unchanged HTML
    assert result == html


def test_process_refs_footnote_reference_without_definition():
    """Test process_refs with footnote reference but no definition"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = "<p>Text with footnote[^1] but no definition.</p>"

    result = converter.process_refs(html)

    # Should return unchanged since no footnote definitions found
    assert result == html
    assert "[^1]" in result


def test_process_refs_footnote_definition_without_reference():
    """Test process_refs with footnote definition but no reference"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = """<p>Text without footnote reference.</p>
[^1]: Orphaned footnote definition with <a href="http://example.com">link</a>."""

    result = converter.process_refs(html)

    # Should remove the footnote definition but leave text unchanged
    assert "Text without footnote reference." in result
    assert "[^1]: Orphaned footnote" not in result


def test_process_refs_reused_footnote_references():
    """Test footnote processing with the same footnote referenced multiple times"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = """<p>First reference[^1] and second reference[^1] to same footnote.</p>
[^1]: Shared footnote with <a href="http://example.com">link</a>."""

    result = converter.process_refs(html)

    # Both references should be converted to the same superscript link
    expected_link = '<a id="test" href="http://example.com"><sup>1</sup></a>'
    assert result.count(expected_link) == 2
    assert "[^1]: Shared footnote" not in result


def test_process_refs_higher_numbered_footnotes():
    """Test footnote processing with higher numbered footnotes"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = """<p>Text with footnote[^5] and another[^9].</p>
[^5]: Fifth footnote with <a href="http://example5.com">link5</a>.
[^9]: Ninth footnote with <a href="http://example9.com">link9</a>."""

    result = converter.process_refs(html)

    # Should handle higher numbers correctly
    assert '<a id="test" href="http://example5.com"><sup>5</sup></a>' in result
    assert '<a id="test" href="http://example9.com"><sup>9</sup></a>' in result
    assert "[^5]: Fifth footnote" not in result
    assert "[^9]: Ninth footnote" not in result


def test_process_refs_footnote_with_no_href():
    """Test process_refs behavior when footnote definition has no href"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = """<p>Text with footnote[^1].</p>
[^1]: Footnote without href link, just plain text."""

    # This should raise an AttributeError when trying to access .group(1) on None
    with pytest.raises(AttributeError):
        converter.process_refs(html)


def test_process_refs_footnote_with_empty_href():
    """Test footnote processing with empty href attribute"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = """<p>Text with footnote[^1].</p>
[^1]: Footnote with <a href="">empty href</a>."""

    result = converter.process_refs(html)

    # Should handle empty href
    assert '<a id="test" href=""><sup>1</sup></a>' in result
    assert "[^1]: Footnote with" not in result


def test_process_refs_footnote_with_relative_url():
    """Test footnote processing with relative URL"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = """<p>Text with footnote[^1].</p>
[^1]: Footnote with <a href="/relative/path">relative link</a>."""

    result = converter.process_refs(html)

    # Should preserve relative URL
    assert '<a id="test" href="/relative/path"><sup>1</sup></a>' in result
    assert "[^1]: Footnote with" not in result


def test_process_refs_footnote_with_anchor_link():
    """Test footnote processing with anchor/fragment URL"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = """<p>Text with footnote[^1].</p>
[^1]: Footnote with <a href="#section-anchor">anchor link</a>."""

    result = converter.process_refs(html)

    # Should preserve anchor URL
    assert '<a id="test" href="#section-anchor"><sup>1</sup></a>' in result
    assert "[^1]: Footnote with" not in result


def test_process_refs_footnote_definition_with_html_formatting():
    """Test footnote processing when definition contains HTML formatting"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = """<p>Text with footnote[^1].</p>
[^1]: Footnote with <strong>bold</strong> and <em>italic</em> text plus <a href="http://example.com">link</a>."""

    result = converter.process_refs(html)

    # Should extract href and remove entire footnote definition including formatting
    assert '<a id="test" href="http://example.com"><sup>1</sup></a>' in result
    assert "[^1]: Footnote with <strong>bold</strong>" not in result
    assert (
        "<strong>bold</strong>" not in result
    )  # Entire footnote definition should be removed


def test_process_refs_integration_example():
    """Integration test showing footnotes in a realistic document"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)

    html = """<h1>Research Paper</h1>
<p>According to recent studies[^1], the technique has been proven effective. However, some researchers disagree[^2].</p>
<p>Additional evidence can be found in multiple sources[^1][^3].</p>
[^1]: Smith, J. (2023). <a href="http://journal.example.com/article1">Effective Techniques in Modern Research</a>. Journal of Science.
[^2]: Brown, A. (2023). <a href="http://journal.example.com/article2">Questioning Modern Research Methods</a>. Critical Review.
[^3]: Davis, M. (2023). <a href="http://journal.example.com/article3">Supporting Evidence for New Techniques</a>. Research Today."""

    result = converter.process_refs(html)

    # Should convert all footnote references and remove all definitions
    assert (
        '<a id="test" href="http://journal.example.com/article1"><sup>1</sup></a>'
        in result
    )
    assert (
        '<a id="test" href="http://journal.example.com/article2"><sup>2</sup></a>'
        in result
    )
    assert (
        '<a id="test" href="http://journal.example.com/article3"><sup>3</sup></a>'
        in result
    )

    # Multiple references to same footnote should all be converted
    assert (
        result.count(
            '<a id="test" href="http://journal.example.com/article1"><sup>1</sup></a>'
        )
        == 2
    )

    # All footnote definitions should be removed
    assert "[^1]: Smith, J." not in result
    assert "[^2]: Brown, A." not in result
    assert "[^3]: Davis, M." not in result

    # Main content should be preserved
    assert "Research Paper" in result
    assert "recent studies" in result
    assert "some researchers disagree" in result
