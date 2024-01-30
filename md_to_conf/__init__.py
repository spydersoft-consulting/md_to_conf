#!/usr/bin/env python3
import logging
import sys
import os
import re
import argparse
import typing
from .client import ConfluenceApiClient
from .converter import MarkdownConverter


def add_attachments(
    file: str, page_id: int, files: typing.List[str], client: ConfluenceApiClient
):
    """
    Add attachments for an array of files

    Args:
       file: markdown file
        page_id: Confluence page id
        files: list of files to attach to the given Confluence page
    """
    source_folder = os.path.dirname(os.path.abspath(file))

    if files:
        for file in files:
            client.upload_attachment(page_id, os.path.join(source_folder, file), "")


def add_images(
    file: str, confluence_api: str, page_id: int, html: str, client: ConfluenceApiClient
) -> str:
    """
    Scan for images and upload as attachments if found

    Args:
        file: markdown file
        page_id: Confluence page id
        html: html string
    Returns:
        html with modified image reference
    """
    source_folder = os.path.dirname(os.path.abspath(file))
    for tag in re.findall(r"<img(.*?)\/>", html):
        rel_path = re.search(r'src="(.*?)"', tag).group(1)
        alt_text = re.search(r'alt="(.*?)"', tag).group(1)
        abs_path = os.path.join(source_folder, rel_path)
        basename = os.path.basename(rel_path)
        client.upload_attachment(page_id, abs_path, alt_text)
        if re.search(r"http.*", rel_path) is None:
            if confluence_api.endswith("/wiki"):
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
    source: str,
    page_id: int,
    space_id: int,
    title: str,
    html: str,
    converter: MarkdownConverter,
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
    LOGGER = logging.getLogger(__name__)
    ref_prefixes = {"default": "#", "bitbucket": "#markdown-header-"}
    ref_postfixes = {"default": "_%d", "bitbucket": "_%d"}

    # We ignore local references in case of unknown or unspecified markdown source
    if source not in ref_prefixes or source not in ref_postfixes:
        LOGGER.warning(
            "Local references weren't"
            "processed because "
            "--markdownsrc wasn"
            "t set or specified source isn"
            "t supported"
        )
        return html

    ref_prefix = ref_prefixes[source]
    ref_postfix = ref_postfixes[source]

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


def get_properties_to_update(
    version: str, props: dict, client, page_id: int
) -> typing.List[any]:
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
            "v%d" % version
        ):
            properties_for_update.append(
                {
                    "key": "editor",
                    "version": existing_prop["version"]["number"] + 1,
                    "value": ("v%d" % version),
                    "id": existing_prop["id"],
                }
            )

    if not props:
        return properties_for_update

    for key in props:
        found = False
        for existing_prop in properties:
            if existing_prop["key"] == key:
                properties_for_update.append(
                    {
                        "key": key,
                        "version": existing_prop["version"]["number"] + 1,
                        "value": props[key],
                        "id": existing_prop["id"],
                    }
                )
                found = True
        if not found:
            properties_for_update.append(
                {"key": key, "version": 1, "value": props[key]}
            )

    return properties_for_update


def get_parser():
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
        "-a",
        "--ancestor",
        help="Parent page under which page will be created or moved.",
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
        "-l",
        "--loglevel",
        default="INFO",
        help="Use this option to set the log verbosity.",
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

    return PARSER


def validate_args(user_name, api_key, markdown_file, org_name):
    LOGGER = logging.getLogger(__name__)
    if user_name is None:
        LOGGER.error("Error: Username not specified by environment variable or option.")
        sys.exit(1)

    if api_key is None:
        LOGGER.error("Error: API key not specified by environment variable or option.")
        sys.exit(1)

    if not os.path.exists(markdown_file):
        LOGGER.error("Error: Markdown file: %s does not exist.", markdown_file)
        sys.exit(1)

    if org_name is None:
        LOGGER.error("Error: Org Name not specified by environment variable or option.")
        sys.exit(1)


def get_confluence_api_url(org_name, no_ssl):
    url = ""
    if org_name is not None:
        if org_name.find(".") != -1:
            url = "https://%s" % org_name
        else:
            url = "https://%s.atlassian.net/wiki" % org_name
    if no_ssl:
        url.replace("https://", "http://")
    return url


def get_space_key(space_key, user_name):
    if space_key is None:
        return "~%s" % (user_name)

    return space_key


def get_parent_page(client, ancestor):
    LOGGER = logging.getLogger(__name__)
    parent_page_id = 0
    if ancestor:
        parent_page = client.get_page(ancestor)
        if parent_page:
            parent_page_id = parent_page.id
        else:
            LOGGER.error("Error: Parent page does not exist: %s", ancestor)
            sys.exit(1)
    return parent_page_id


def main():
    """
    Main program

    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - \
        %(levelname)s - %(funcName)s [%(lineno)d] - \
        %(message)s",
    )
    LOGGER = logging.getLogger(__name__)

    # ArgumentParser to parse arguments and options
    PARSER = get_parser()

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

        validate_args(USERNAME, API_KEY, MARKDOWN_FILE, ORGNAME)

        SPACE_KEY = get_space_key(SPACE_KEY, USERNAME)

        CONFLUENCE_API_URL = get_confluence_api_url(ORGNAME, NOSSL)

    except Exception as err:
        LOGGER.error("\n\nException caught:\n%s ", err)
        LOGGER.error("\nFailed to process command line arguments. Exiting.")
        sys.exit(1)

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

    html = converter.convert_md_to_conf_html(
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

    parent_page_id = get_parent_page(client, ANCESTOR)

    if page.id == 0:
        page = client.create_page(title, html, parent_page_id)

    LOGGER.info("Page Id %d" % page.id)
    html = add_images(MARKDOWN_FILE, CONFLUENCE_API_URL, page.id, html, client)
    # Add local references
    html = add_local_refs(
        MARKDOWN_SOURCE, page.id, page.spaceId, title, html, converter
    )

    client.update_page(page.id, title, html, page.version, parent_page_id)

    properties_for_update = get_properties_to_update(
        VERSION, PROPERTIES, client, page.id
    )
    if len(properties_for_update) > 0:
        LOGGER.info(
            "Updating %s page content properties..." % len(properties_for_update)
        )

        for prop in properties_for_update:
            client.update_page_property(page.id, prop)

    if LABELS:
        client.update_labels(page.id, LABELS)

    if ATTACHMENTS:
        add_attachments(MARKDOWN_FILE, page.id, ATTACHMENTS, client)

    LOGGER.info("Markdown Converter completed successfully.")
