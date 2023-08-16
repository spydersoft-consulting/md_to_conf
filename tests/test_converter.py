import pytest
import codecs
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


def test_converter_basic(test_converter: MarkdownConverter):
    html = test_converter.get_html_from_markdown()

    snapshot = get_snapshot("basic-md-raw.html")

    # with open("tests/testfiles/basic.html", "w") as f:
    #     f.write(html)

    assert html == snapshot


def test_slug(test_converter: MarkdownConverter):
    slug = test_converter.slug("<tag>The $slug</tag>", False)
    assert slug == "The-slug"


def test_slug_lower(test_converter: MarkdownConverter):
    slug = test_converter.slug("<tag>The $slug</tag>", True)
    assert slug == "the-slug"


def get_snapshot(file: str):
    fullFile = "tests/testfiles/%s" % file
    with codecs.open(fullFile, "r", "utf-8") as mdfile:
        return mdfile.read()
