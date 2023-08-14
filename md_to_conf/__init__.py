#!/usr/bin/env python3
import logging
import sys
import os
import re
import argparse
import typing
from .client import ConfluenceApiClient
from .converter import MarkdownConverter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - \
%(levelname)s - %(funcName)s [%(lineno)d] - \
%(message)s",
)
LOGGER = logging.getLogger(__name__)

# ArgumentParser to parse arguments and options
PARSER = argparse.ArgumentParser()
PARSER.add_argument(
    "markdownFile", help="Full path of the markdown file to convert and upload."
)
PARSER.add_argument(
    "spacekey",
    help="Confluence Space key for the page. If omitted, will use user space.",
)
PARSER.add_argument(
    "-u", "--username", help="Confluence username if $CONFLUENCE_USERNAME not set."
)
PARSER.add_argument(
    "-p", "--apikey", help="Confluence API key if $CONFLUENCE_API_KEY not set."
)
PARSER.add_argument(
    "-o",
    "--orgname",
    help="Confluence organisation if $CONFLUENCE_ORGNAME not set. "
    "e.g. https://XXX.atlassian.net/wiki"
    "If orgname contains a dot, considered as the fully qualified domain name."
    "e.g. https://XXX",
)
PARSER.add_argument(
    "-a", "--ancestor", help="Parent page under which page will be created or moved."
)
PARSER.add_argument(
    "-t",
    "--attachment",
    nargs="+",
    help="Attachment(s) to upload to page. Paths relative to the markdown file.",
)
PARSER.add_argument(
    "-c",
    "--contents",
    action="store_true",
    default=False,
    help="Use this option to generate a contents page.",
)
PARSER.add_argument(
    "-n",
    "--nossl",
    action="store_true",
    default=False,
    help="Use this option if NOT using SSL. Will use HTTP instead of HTTPS.",
)
PARSER.add_argument(
    "-d",
    "--delete",
    action="store_true",
    default=False,
    help="Use this option to delete the page instead of create it.",
)
PARSER.add_argument(
    "-l", "--loglevel", default="INFO", help="Use this option to set the log verbosity."
)
PARSER.add_argument(
    "-s",
    "--simulate",
    action="store_true",
    default=False,
    help="Use this option to only show conversion result.",
)
PARSER.add_argument(
    "-v",
    "--version",
    type=int,
    action="store",
    default=2,
    help="Version of confluence page (default is 2).",
)
PARSER.add_argument(
    "-mds",
    "--markdownsrc",
    action="store",
    default="default",
    choices=["default", "bitbucket"],
    help="Use this option to specify a markdown source "
    " (i.e. what processor this markdown was targeting). "
    "Possible values: bitbucket.",
)
PARSER.add_argument(
    "--label",
    action="append",
    dest="labels",
    default=[],
    help="A list of labels to set on the page.",
)
PARSER.add_argument(
    "--property",
    action="append",
    dest="properties",
    default=[],
    type=lambda kv: kv.split("="),
    help="A list of content properties to set on the page.",
)
PARSER.add_argument(
    "--title",
    action="store",
    dest="title",
    default=None,
    help="Set the title for the page, otherwise the title is "
    "going to be the first line in the markdown file",
)
PARSER.add_argument(
    "--remove-emojies",
    action="store_true",
    dest="remove_emojies",
    default=False,
    help="Remove emojies if there are any. This may be need if "
    "the database doesn't support emojies",
)

ARGS = PARSER.parse_args()

# Assign global variables
try:
    # Set log level
    LOGGER.setLevel(getattr(logging, ARGS.loglevel.upper(), None))

    MARKDOWN_FILE = ARGS.markdownFile
    SPACE_KEY = ARGS.spacekey
    USERNAME = os.getenv("CONFLUENCE_USERNAME", ARGS.username)
    API_KEY = os.getenv("CONFLUENCE_API_KEY", ARGS.apikey)
    ORGNAME = os.getenv("CONFLUENCE_ORGNAME", ARGS.orgname)
    ANCESTOR = ARGS.ancestor
    NOSSL = ARGS.nossl
    DELETE = ARGS.delete
    SIMULATE = ARGS.simulate
    VERSION = ARGS.version
    MARKDOWN_SOURCE = ARGS.markdownsrc
    LABELS = ARGS.labels
    PROPERTIES = dict(ARGS.properties)
    ATTACHMENTS = ARGS.attachment
    CONTENTS = ARGS.contents
    TITLE = ARGS.title
    REMOVE_EMOJIES = ARGS.remove_emojies

    if USERNAME is None:
        LOGGER.error("Error: Username not specified by environment variable or option.")
        sys.exit(1)

    if API_KEY is None:
        LOGGER.error("Error: API key not specified by environment variable or option.")
        sys.exit(1)

    if not os.path.exists(MARKDOWN_FILE):
        LOGGER.error("Error: Markdown file: %s does not exist.", MARKDOWN_FILE)
        sys.exit(1)

    if SPACE_KEY is None:
        SPACE_KEY = "~%s" % (USERNAME)

    if ORGNAME is not None:
        if ORGNAME.find(".") != -1:
            CONFLUENCE_API_URL = "https://%s" % ORGNAME
        else:
            CONFLUENCE_API_URL = "https://%s.atlassian.net/wiki" % ORGNAME
    else:
        LOGGER.error("Error: Org Name not specified by environment variable or option.")
        sys.exit(1)

    if NOSSL:
        CONFLUENCE_API_URL.replace("https://", "http://")

except Exception as err:
    LOGGER.error("\n\nException caught:\n%s ", err)
    LOGGER.error("\nFailed to process command line arguments. Exiting.")
    sys.exit(1)


def add_attachments(page_id: int, files: typing.List[str], client: ConfluenceApiClient):
    """
    Add attachments for an array of files

    Args:
        page_id: Confluence page id
        files: list of files to attach to the given Confluence page
    """
    source_folder = os.path.dirname(os.path.abspath(MARKDOWN_FILE))

    if files:
        for file in files:
            client.upload_attachment(page_id, os.path.join(source_folder, file), "")


def add_images(page_id: int, html: str, client: ConfluenceApiClient) -> str:
    """
    Scan for images and upload as attachments if found

    Args:
        page_id: Confluence page id
        html: html string
    Returns:
        html with modified image reference
    """
    source_folder = os.path.dirname(os.path.abspath(MARKDOWN_FILE))

    for tag in re.findall(r"<img(.*?)\/>", html):
        rel_path = re.search(r'src="(.*?)"', tag).group(1)
        alt_text = re.search(r'alt="(.*?)"', tag).group(1)
        abs_path = os.path.join(source_folder, rel_path)
        basename = os.path.basename(rel_path)
        client.upload_attachment(page_id, abs_path, alt_text)
        if re.search(r"http.*", rel_path) is None:
            if CONFLUENCE_API_URL.endswith("/wiki"):
                html = html.replace(
                    "%s" % (rel_path),
                    "/wiki/download/attachments/%d/%s" % (page_id, basename),
                )
            else:
                html = html.replace(
                    "%s" % (rel_path),
                    "/download/attachments/%d/%s" % (page_id, basename),
                )
    return html


def add_local_refs(
    page_id: int, space_id: int, title: str, html: str, converter: MarkdownConverter
) -> str:
    """
    Convert local links to correct confluence local links

    Args:
        page_id: Page ID
        space_id: Space ID
        title: Page Title
        html: string representing page HTML
        converter: an instance of the MarkdownConverter for this page
    Returns:
        modified html string
    """

    ref_prefixes = {"default": "#", "bitbucket": "#markdown-header-"}
    ref_postfixes = {"default": "_%d", "bitbucket": "_%d"}

    # We ignore local references in case of unknown or unspecified markdown source
    if MARKDOWN_SOURCE not in ref_prefixes or MARKDOWN_SOURCE not in ref_postfixes:
        LOGGER.warning(
            "Local references weren't"
            "processed because "
            "--markdownsrc wasn"
            "t set or specified source isn"
            "t supported"
        )
        return html

    ref_prefix = ref_prefixes[MARKDOWN_SOURCE]
    ref_postfix = ref_postfixes[MARKDOWN_SOURCE]

    LOGGER.info("Converting confluence local links...")

    headers = re.findall(r"<h\d+>(.*?)</h\d+>", html, re.DOTALL)

    if not headers:
        return html

    headers_map = converter.process_headers(ref_prefix, ref_postfix, headers)

    links = re.findall(r'<a href="#.+?">.+?</a>', html)

    if not links:
        return html

    html = converter.process_links(html, links, headers_map, space_id, page_id, title)

    return html


def get_properties_to_update(client, page_id: int) -> typing.List[any]:
    """
    Get a list of properties which have changed

    Args:
        page_id: integer
    Returns:
        array of properties to update
    """
    properties = client.get_page_properties(page_id)
    properties_for_update = []
    for existing_prop in properties:
        # Change the editor version
        if existing_prop["key"] == "editor" and existing_prop["value"] != (
            "v%d" % VERSION
        ):
            properties_for_update.append(
                {
                    "key": "editor",
                    "version": existing_prop["version"]["number"] + 1,
                    "value": ("v%d" % VERSION),
                    "id": existing_prop["id"],
                }
            )

    if not PROPERTIES:
        return properties_for_update

    for key in PROPERTIES:
        found = False
        for existing_prop in properties:
            if existing_prop["key"] == key:
                properties_for_update.append(
                    {
                        "key": key,
                        "version": existing_prop["version"]["number"] + 1,
                        "value": PROPERTIES[key],
                        "id": existing_prop["id"],
                    }
                )
                found = True
        if not found:
            properties_for_update.append(
                {"key": key, "version": 1, "value": PROPERTIES[key]}
            )

    return properties_for_update


def main():
    """
    Main program

    """

    LOGGER.info("\t----------------------------------")
    LOGGER.info("\tMarkdown to Confluence Upload Tool")
    LOGGER.info("\t----------------------------------")

    LOGGER.info("Markdown file:\t%s", MARKDOWN_FILE)
    LOGGER.info("Space Key:\t%s", SPACE_KEY)

    converter = MarkdownConverter(
        MARKDOWN_FILE, CONFLUENCE_API_URL, MARKDOWN_SOURCE, VERSION
    )

    if TITLE:
        title = TITLE
        has_title = True
    else:
        with open(MARKDOWN_FILE, "r") as mdfile:
            title = mdfile.readline().lstrip("#").strip()
            mdfile.seek(0)
        has_title = False

    html = converter.get_html_from_markdown(
        has_title=has_title,
        remove_emojies=REMOVE_EMOJIES,
        add_contents=CONTENTS,
    )

    LOGGER.debug("html: %s", html)

    if SIMULATE:
        LOGGER.info("Simulate mode is active - stop processing here.")
        sys.exit(0)

    client = ConfluenceApiClient(
        CONFLUENCE_API_URL, USERNAME, API_KEY, SPACE_KEY, VERSION, not NOSSL
    )

    LOGGER.info("Checking if Atlas page exists...")
    page = client.get_page(title)

    if DELETE and page:
        client.delete_page(page.id)
        sys.exit(1)

    parent_page_id = 0

    if ANCESTOR:
        parent_page = client.get_page(ANCESTOR)
        if parent_page:
            parent_page_id = parent_page.id
        else:
            LOGGER.error("Error: Parent page does not exist: %s", ANCESTOR)
            sys.exit(1)

    if page.id == 0:
        page = client.create_page(title, html, parent_page_id)

    LOGGER.info("Page Id %d" % page.id)

    html = add_images(page.id, html, client)
    # Add local references
    html = add_local_refs(page.id, page.spaceId, title, html, converter)

    client.update_page(page.id, title, html, page.version, parent_page_id)

    properties_for_update = get_properties_to_update(client, page.id)
    if len(properties_for_update) > 0:
        LOGGER.info(
            "Updating %s page content properties..." % len(properties_for_update)
        )

        for prop in properties_for_update:
            client.update_page_property(page.id, prop)

    if LABELS:
        client.update_labels(page.id, LABELS)

    if ATTACHMENTS:
        add_attachments(page.id, ATTACHMENTS, client)

    LOGGER.info("Markdown Converter completed successfully.")


if __name__ == "__main__":
    main()
