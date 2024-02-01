#!/usr/bin/env python3
import logging
import sys
import os
import argparse
from .confluence_converter import ConfluenceConverter
from .client import ConfluenceApiClient
from .converter import MarkdownConverter


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


def main():
    """
    Main program

    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - \
        %(levelname)s - %(funcName)s [%(lineno)d] - \
        \t%(message)s",
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

    except Exception as err:
        LOGGER.error("\n\nException caught:\n%s ", err)
        LOGGER.error("\nFailed to process command line arguments. Exiting.")
        sys.exit(1)

    LOGGER.info("\t----------------------------------")
    LOGGER.info("\tMarkdown to Confluence Upload Tool")
    LOGGER.info("\t----------------------------------")

    LOGGER.info("Markdown file:\t%s", MARKDOWN_FILE)
    LOGGER.info("Space Key:\t%s", SPACE_KEY)

    confluence_converter: ConfluenceConverter = ConfluenceConverter(
        MARKDOWN_FILE,
        MARKDOWN_SOURCE,
        TITLE,
        ORGNAME,
        not NOSSL,
        USERNAME,
        SPACE_KEY,
        API_KEY,
        ANCESTOR,
        VERSION,
    )

    confluence_converter.convert(
        SIMULATE, DELETE, REMOVE_EMOJIES, CONTENTS, LABELS, PROPERTIES, ATTACHMENTS
    )
