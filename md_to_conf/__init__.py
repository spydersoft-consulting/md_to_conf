#!/usr/bin/env python3
import glob
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
        "markdownFile",
        nargs="+",
        help=(
            "One or more Markdown files to convert and upload. "
            "Glob patterns are supported (e.g. 'docs/*.md').  "
            "When multiple files are given, cross-document links "
            "between them are automatically resolved to Confluence URLs."
        ),
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
        help="Use this option to set the log verbosity. Choices: DEBUG, INFO, WARNING, ERROR. Default: INFO.",
    )
    PARSER.add_argument(
        "-V",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose (DEBUG-level) logging. Shorthand for --loglevel DEBUG.",
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
    PARSER.add_argument(
        "--mermaid",
        action="store_true",
        dest="render_mermaid",
        default=False,
        help=(
            "Render mermaid code blocks as PNG images before uploading. "
            "Uses the local 'mmdc' CLI if available on PATH, otherwise "
            "falls back to the mermaid.ink public API (requires internet)."
        ),
    )
    PARSER.add_argument(
        "--exclude",
        action="append",
        dest="exclude_patterns",
        default=[],
        metavar="PATTERN",
        help=(
            "Glob pattern of files to exclude from publishing. "
            "Can be specified multiple times. "
            "Example: --exclude 'docs/draft*.md' --exclude 'docs/wip/**'. "
            "Inline exclusions using a '!' prefix in the file list are also "
            "supported, e.g. '!docs/draft.md'."
        ),
    )

    return PARSER


def validate_args(user_name, api_key, markdown_files, org_name):
    LOGGER = logging.getLogger(__name__)
    if user_name is None:
        LOGGER.error("Error: Username not specified by environment variable or option.")
        sys.exit(1)

    if api_key is None:
        LOGGER.error("Error: API key not specified by environment variable or option.")
        sys.exit(1)

    for markdown_file in markdown_files:
        if not os.path.exists(markdown_file):
            LOGGER.error("Error: Markdown file: %s does not exist.", markdown_file)
            sys.exit(1)

    if org_name is None:
        LOGGER.error("Error: Org Name not specified by environment variable or option.")
        sys.exit(1)


def _expand_include_patterns(patterns):
    """
    Expand a list of include glob patterns into a de-duplicated, ordered
    list of absolute paths.  Patterns that match no files are treated as
    literal paths so that validate_args can report the missing file.
    """
    expanded = []
    seen = set()
    for pattern in patterns:
        matches = sorted(glob.glob(pattern, recursive=True))
        if matches:
            for path in matches:
                abs_path = os.path.abspath(path)
                if abs_path not in seen:
                    seen.add(abs_path)
                    expanded.append(abs_path)
        else:
            abs_path = os.path.abspath(pattern)
            if abs_path not in seen:
                seen.add(abs_path)
                expanded.append(abs_path)
    return expanded


def expand_file_globs(patterns, exclude_patterns=None):
    """
    Expand a list of file path patterns into a de-duplicated, ordered list
    of absolute paths, then remove any paths that match an exclusion pattern.

    Include patterns:
      - Standard file paths or shell globs (``docs/*.md``, ``**/*.md``).
      - A pattern prefixed with ``!`` is treated as an exclusion instead of
        an include, e.g. ``!docs/draft.md`` or ``!drafts/**``.

    Exclusion patterns (applied last, highest precedence):
      - Passed via the ``exclude_patterns`` argument (populated from the
        ``--exclude`` CLI flag).
      - Also accepted inline as ``!``-prefixed entries in *patterns*.

    Patterns that match no files are treated as literal paths (so the
    missing-file error is reported by validate_args for include patterns;
    non-matching exclude patterns are silently ignored).
    """
    include = [p for p in patterns if not p.startswith("!")]
    inline_excludes = [p[1:] for p in patterns if p.startswith("!")]
    all_excludes = list(inline_excludes) + list(exclude_patterns or [])

    # Build the excluded set
    excluded = set()
    for pattern in all_excludes:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            for path in matches:
                excluded.add(os.path.abspath(path))
        else:
            # Treat as a literal path
            excluded.add(os.path.abspath(pattern))

    expanded = _expand_include_patterns(include)
    return [p for p in expanded if p not in excluded]


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
        # Set log level — --verbose overrides --loglevel.
        # The root logger level must be lowered so that DEBUG messages from
        # all sub-modules (client, converter, …) are not silently dropped
        # before they reach any handler.
        if ARGS.verbose:
            log_level = logging.DEBUG
        else:
            log_level = getattr(logging, ARGS.loglevel.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        LOGGER.setLevel(log_level)

        MARKDOWN_FILES = expand_file_globs(ARGS.markdownFile, ARGS.exclude_patterns)
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
        RENDER_MERMAID = ARGS.render_mermaid

        validate_args(USERNAME, API_KEY, MARKDOWN_FILES, ORGNAME)

    except Exception as err:
        LOGGER.error("\n\nException caught:\n%s ", err)
        LOGGER.error("\nFailed to process command line arguments. Exiting.")
        sys.exit(1)

    LOGGER.info("\t----------------------------------")
    LOGGER.info("\tMarkdown to Confluence Upload Tool")
    LOGGER.info("\t----------------------------------")
    LOGGER.info("Files to process:\t%d", len(MARKDOWN_FILES))
    LOGGER.info("Space Key:\t%s", SPACE_KEY)
    if ANCESTOR:
        LOGGER.info("Ancestor:\t%s", ANCESTOR)
    LOGGER.debug("Org/URL:\t%s", ORGNAME)
    LOGGER.debug("Username:\t%s", USERNAME)
    if ARGS.verbose:
        LOGGER.debug("Verbose logging is enabled (DEBUG level).")

    multi_file = len(MARKDOWN_FILES) > 1

    # ── Build ConfluenceConverter instances (one per file) ─────────────────
    converters = []
    for md_file in MARKDOWN_FILES:
        LOGGER.info("Processing:\t%s", md_file)
        cc = ConfluenceConverter(
            md_file,
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
        converters.append((md_file, cc))

    # ── Pass 1: publish all pages, collect page_map ──────────────────────
    # When multi_file is True we run a first pass without cross-file link
    # resolution so that ALL page IDs are known before the second pass.
    page_map: dict = {}  # abs_path → {"page_id": int, "title": str, "url": str}

    for md_file, cc in converters:
        LOGGER.info("Pass 1 — publishing:\t%s", md_file)
        result = cc.convert(
            SIMULATE,
            DELETE,
            REMOVE_EMOJIES,
            CONTENTS,
            LABELS,
            PROPERTIES,
            ATTACHMENTS,
            render_mermaid=RENDER_MERMAID,
            page_map=None,  # no cross-file resolution yet
        )
        if result is not None:
            page_map[os.path.abspath(md_file)] = result

    # ── Pass 2 (multi-file only): re-update pages with cross-file links ───
    if multi_file and page_map and not SIMULATE and not DELETE:
        LOGGER.info(
            "Pass 2 — resolving cross-file links across %d pages …",
            len(page_map),
        )
        for md_file, cc in converters:
            LOGGER.info("Pass 2 — updating:\t%s", md_file)
            cc.convert(
                SIMULATE,
                DELETE,
                REMOVE_EMOJIES,
                CONTENTS,
                LABELS,
                PROPERTIES,
                ATTACHMENTS,
                render_mermaid=RENDER_MERMAID,
                page_map=page_map,
            )
