import pytest
from md_to_conf import MarkdownConverter


@pytest.fixture
def test_converter() -> MarkdownConverter:
    return MarkdownConverter(
        "tests/testfiles/basic.md", "https://domain.confluence.net/wiki", "default", 2
    )


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


def test_converter_basic(test_converter: MarkdownConverter, snapshot):
    html = test_converter.get_html_from_markdown()
    assert html == snapshot


def test_slug(test_converter: MarkdownConverter):
    slug = test_converter.slug("<tag>The $slug</tag>", False)
    assert slug == "The-slug"


def test_slug_lower(test_converter: MarkdownConverter):
    slug = test_converter.slug("<tag>The $slug</tag>", True)
    assert slug == "the-slug"


def test_convert_comment_block(test_converter: MarkdownConverter):
    slug = test_converter.convert_comment_block("<!-- some comments go here -->")
    assert slug == "<ac:placeholder> some comments go here </ac:placeholder>"


def test_toc_convert(test_converter: MarkdownConverter, snapshot):
    slug = test_converter.create_table_of_content(
        "<h1>First heading</h1> <p>[TOC]</p> <h2>Second heading</h2>"
    )

    assert slug == snapshot
