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
