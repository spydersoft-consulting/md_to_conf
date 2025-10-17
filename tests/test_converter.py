import pytest
from md_to_conf import MarkdownConverter


URL = "https://domain.confluence.net/wiki"


@pytest.fixture
def test_converter_basic() -> MarkdownConverter:
    return MarkdownConverter("tests/testfiles/basic.md", URL, "default", 2)


@pytest.fixture
def test_converter_advanced() -> MarkdownConverter:
    return MarkdownConverter("tests/testfiles/advanced.md", URL, "default", 2)


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
    
    html = '<p>See <a href="#section-1">Section 1</a> and <a href="#section-2">Section 2</a> for details</p>'
    links = ['<a href="#section-1">Section 1</a>', '<a href="#section-2">Section 2</a>']
    headers_map = {
        "#section-1": "Section1",
        "#section-2": "Section2"
    }
    space_key = "TEST"
    page_id = 12345
    title = "Test Page"
    
    result = converter.process_links(html, links, headers_map, space_key, page_id, title)
    
    expected_replacement1 = ('<ac:link ac:anchor="Section1">'
                           '<ac:plain-text-link-body>'
                           '<![CDATA[Section 1]]></ac:plain-text-link-body></ac:link>')
    expected_replacement2 = ('<ac:link ac:anchor="Section2">'
                           '<ac:plain-text-link-body>'
                           '<![CDATA[Section 2]]></ac:plain-text-link-body></ac:link>')
    
    assert expected_replacement1 in result
    assert expected_replacement2 in result


def test_process_links_editor_v2():
    """Test process_links function with editor version 2"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)
    
    html = '<p>See <a href="#section-1">Section 1</a> and <a href="#section-2">Section 2</a> for details</p>'
    links = ['<a href="#section-1">Section 1</a>', '<a href="#section-2">Section 2</a>']
    headers_map = {
        "#section-1": "Section-1",
        "#section-2": "Section-2"
    }
    space_key = "TEST"
    page_id = 12345
    title = "Test Page"
    
    result = converter.process_links(html, links, headers_map, space_key, page_id, title)
    
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
    
    result = converter.process_links(html, links, headers_map, space_key, page_id, title)
    
    expected_replacement = '<a href="https://example.com/wiki/spaces/TEST/pages/12345/Test+Page+With+Spaces#Section-1" title="Section 1">Section 1</a>'
    assert expected_replacement in result


def test_process_links_with_html_tags_in_alt_text_v1():
    """Test process_links function with HTML tags in alt text for editor v1"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 1)
    
    html = '<p>See <a href="#section-1"><strong>Bold</strong> Section</a> for details</p>'
    links = ['<a href="#section-1"><strong>Bold</strong> Section</a>']
    headers_map = {"#section-1": "Section1"}
    space_key = "TEST"
    page_id = 12345
    title = "Test Page"
    
    result = converter.process_links(html, links, headers_map, space_key, page_id, title)
    
    # HTML tags should be stripped from alt text in editor v1
    expected_replacement = ('<ac:link ac:anchor="Section1">'
                          '<ac:plain-text-link-body>'
                          '<![CDATA[ Section]]></ac:plain-text-link-body></ac:link>')
    
    assert expected_replacement in result


def test_process_links_with_html_tags_in_alt_text_v2():
    """Test process_links function with HTML tags in alt text for editor v2"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)
    
    html = '<p>See <a href="#section-1"><strong>Bold</strong> Section</a> for details</p>'
    links = ['<a href="#section-1"><strong>Bold</strong> Section</a>']
    headers_map = {"#section-1": "Section-1"}
    space_key = "TEST"
    page_id = 12345
    title = "Test Page"
    
    result = converter.process_links(html, links, headers_map, space_key, page_id, title)
    
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
    
    result = converter.process_links(html, links, headers_map, space_key, page_id, title)
    
    # Original link should remain unchanged when not found in headers_map
    assert '<a href="#nonexistent">Missing Link</a>' in result


def test_process_links_empty_links_list():
    """Test process_links function with empty links list"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)
    
    html = '<p>Some content without links</p>'
    links = []
    headers_map = {"#section-1": "Section-1"}
    space_key = "TEST"
    page_id = 12345
    title = "Test Page"
    
    result = converter.process_links(html, links, headers_map, space_key, page_id, title)
    
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
    
    result = converter.process_links(html, links, headers_map, space_key, page_id, title)
    
    expected_replacement = '<a href="https://example.com/wiki/spaces/TEST/pages/12345/Test+Page#Section-1" title="Section 1">Section 1</a>'
    
    # Both instances should be replaced
    assert result.count(expected_replacement) == 2
    assert '<a href="#section-1">Section 1</a>' not in result


def test_process_links_complex_anchor_refs():
    """Test process_links function with complex anchor references"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)
    
    html = '<p>See <a href="#complex-section-with-numbers-123">Complex Section</a> for details</p>'
    links = ['<a href="#complex-section-with-numbers-123">Complex Section</a>']
    headers_map = {"#complex-section-with-numbers-123": "Complex-Section-With-Numbers-123"}
    space_key = "COMPLEX"
    page_id = 98765
    title = "Complex Test Page"
    
    result = converter.process_links(html, links, headers_map, space_key, page_id, title)
    
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
        "#another-section": "AnotherSection"
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
        "#another-section": "Another-Section"
    }
    
    assert result == expected


def test_process_headers_with_html_tags_v1():
    """Test process_headers function with HTML tags in headers for editor v1"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 1)
    
    headers = ["<strong>Bold</strong> Section", "<em>Italic</em> Text", "<code>Code</code> Block"]
    ref_prefix = "#"
    ref_postfix = ".%s"
    
    result = converter.process_headers(ref_prefix, ref_postfix, headers)
    
    expected = {
        "#bold-section": "Section",
        "#italic-text": "Text",
        "#code-block": "Block"
    }
    
    assert result == expected


def test_process_headers_with_html_tags_v2():
    """Test process_headers function with HTML tags in headers for editor v2"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)
    
    headers = ["<strong>Bold</strong> Section", "<em>Italic</em> Text", "<code>Code</code> Block"]
    ref_prefix = "#"
    ref_postfix = ".%s"
    
    result = converter.process_headers(ref_prefix, ref_postfix, headers)
    
    expected = {
        "#bold-section": "Bold-Section",
        "#italic-text": "Italic-Text", 
        "#code-block": "Code-Block"
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
        "#section-1.2": "Section1.2"
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
        "#section-1.2": "Section-1.2"
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
        "#section--more": "Section--More"
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
        "#jsonparser-class": "JSONParser-Class"
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
        "#newlinecharacter": "Newline\nCharacter"
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
        "custom-section-b": "Section-B"
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
        "#rsum-overview": "Rsum-Overview"
    }
    
    assert result == expected


def test_process_headers_complex_html_structure_v1():
    """Test process_headers function with complex HTML structure for editor v1"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 1)
    
    headers = [
        "<h1><strong>Main</strong> <em>Title</em></h1>",
        "<span class='highlight'>Important</span> Section",
        "<a href='#'>Linked</a> Header"
    ]
    ref_prefix = "#"
    ref_postfix = ".%s"
    
    result = converter.process_headers(ref_prefix, ref_postfix, headers)
    
    expected = {
        "#main-title": "",
        "#important-section": "Section",
        "#linked-header": "Header"
    }
    
    assert result == expected


def test_process_headers_complex_html_structure_v2():
    """Test process_headers function with complex HTML structure for editor v2"""
    converter = MarkdownConverter("dummy.md", "https://example.com/wiki", "default", 2)
    
    headers = [
        "<h1><strong>Main</strong> <em>Title</em></h1>",
        "<span class='highlight'>Important</span> Section", 
        "<a href='#'>Linked</a> Header"
    ]
    ref_prefix = "#"
    ref_postfix = ".%s"
    
    result = converter.process_headers(ref_prefix, ref_postfix, headers)
    
    expected = {
        "#main-title": "Main-Title",
        "#important-section": "Important-Section",
        "#linked-header": "Linked-Header"
    }
    
    assert result == expected
