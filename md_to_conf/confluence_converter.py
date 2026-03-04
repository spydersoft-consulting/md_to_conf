import logging
import sys
import typing
import os
import re
from .client import ConfluenceApiClient
from .converter import MarkdownConverter

LOGGER = logging.getLogger(__name__)


class ConfluenceConverter:
    def __init__(
        self,
        file: str,
        md_source: str,
        title: str,
        org_name: str,
        use_ssl: bool,
        user_name: str,
        space_key: str,
        api_key: str,
        ancestor: str,
        version: int,
    ):
        """
        Constructor

        Args:
            client: An instance of the confluence client
        """
        self.file: str = file
        self.md_source: str = md_source
        self.source_folder: str = os.path.dirname(os.path.abspath(file))
        self.org_name: str = org_name
        self.use_ssl: bool = use_ssl
        self.user_name: str = user_name
        self.api_key: str = api_key
        self.version = version
        self.ancestor: str = ancestor
        self.title: str = title

        self.space_key: str = self.get_space_key(space_key)
        self.confluence_client = self.get_client()

    def convert(
        self,
        simulate: bool,
        delete: bool,
        remove_emojies: bool,
        add_contents: bool,
        labels: typing.List[str],
        properties: dict,
        attachments: typing.List[str],
        render_mermaid: bool = False,
        page_map: typing.Optional[typing.Dict[str, dict]] = None,
    ):
        converter = MarkdownConverter(
            self.file, self.get_confluence_api_url(), self.md_source, self.version
        )

        if self.title is not None:
            title = self.title
            has_title = True
        else:
            with open(self.file, "r") as mdfile:
                title = mdfile.readline().lstrip("#").strip()
                mdfile.seek(0)
            has_title = False

        html = converter.convert_md_to_conf_html(
            has_title=has_title,
            remove_emojies=remove_emojies,
            add_contents=add_contents,
            render_mermaid=render_mermaid,
        )

        LOGGER.debug("html: %s", html)

        if simulate:
            LOGGER.info("Simulate mode is active - stop processing here.")
            return

        LOGGER.info("Checking if Atlas page exists...")
        page = self.confluence_client.get_page(title)

        if delete and page is not None and page.id > 0:
            self.confluence_client.delete_page(page.id)
            return

        parent_page_id = self.get_parent_page()

        if page.id == 0:
            page = self.confluence_client.create_page(title, html, parent_page_id)

        LOGGER.info("Page Id %d" % page.id)

        # Upload mermaid-generated images before add_images so they are
        # treated like any other attachment already on the page.
        if render_mermaid and converter.mermaid_images:
            for img_path in converter.mermaid_images:
                self.confluence_client.upload_attachment(page.id, img_path, "")

        html = self.add_images(page.id, html)
        # Add local references
        html = self.add_local_refs(page.id, title, html, converter)

        if page_map:
            html = self.add_cross_file_links(html, page_map)

        self.confluence_client.update_page(
            page.id, title, html, page.version, parent_page_id
        )

        properties_for_update = self.get_properties_to_update(properties, page.id)
        if len(properties_for_update) > 0:
            LOGGER.info(
                "Updating %s page content properties..." % len(properties_for_update)
            )

            for prop in properties_for_update:
                self.confluence_client.update_page_property(page.id, prop)

        if labels is not None and len(labels) > 0:
            self.confluence_client.update_labels(page.id, labels)

        if attachments is not None and len(attachments) > 0:
            self.add_attachments(page.id, attachments)

        LOGGER.info("Markdown Converter completed successfully.")

        # Return published page info for cross-file link resolution
        return {
            "page_id": page.id,
            "title": title,
            "url": "%s/spaces/%s/pages/%d/%s"
            % (
                self.get_confluence_api_url(),
                self.space_key,
                page.id,
                "+".join(title.split()),
            ),
        }

    def add_attachments(self, page_id: int, files: typing.List[str]):
        """
        Add attachments for an array of files

        Args:
            file: markdown file
            page_id: Confluence page id
            files: list of files to attach to the given Confluence page
        """
        if files:
            for file in files:
                self.confluence_client.upload_attachment(
                    page_id, os.path.join(self.source_folder, file), ""
                )

    def add_images(self, page_id: int, html: str) -> str:
        """
        Scan for images and upload as attachments if found

        Args:
            file: markdown file
            page_id: Confluence page id
            html: html string
        Returns:
            html with modified image reference
        """
        for tag in re.findall(r"<img(.*?)\/>", html):
            rel_path = re.search(r'src="(.*?)"', tag).group(1)
            alt_match = re.search(r'alt="(.*?)"', tag)
            alt_text = alt_match.group(1) if alt_match else ""
            if re.search(r"http.*", rel_path) is not None:
                continue
            abs_path = os.path.join(self.source_folder, rel_path)
            basename = os.path.basename(rel_path)
            self.confluence_client.upload_attachment(page_id, abs_path, alt_text)
            if self.get_confluence_api_url().endswith("/wiki"):
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
        self,
        page_id: int,
        title: str,
        html: str,
        converter: MarkdownConverter,
    ) -> str:
        """
        Convert local links to correct confluence local links

        Args:
            page_id: Page ID
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
        if self.md_source not in ref_prefixes or self.md_source not in ref_postfixes:
            LOGGER.warning(
                "Local references weren't"
                "processed because "
                "--markdownsrc wasn"
                "t set or specified source isn"
                "t supported"
            )
            return html

        ref_prefix = ref_prefixes[self.md_source]
        ref_postfix = ref_postfixes[self.md_source]

        LOGGER.info("Converting confluence local links...")

        headers = re.findall(r"<h\d+>(.*?)</h\d+>", html, re.DOTALL)

        if not headers:
            return html

        headers_map = converter.process_headers(ref_prefix, ref_postfix, headers)

        links = re.findall(r'<a href="#.+?">.+?</a>', html)

        if not links:
            return html

        html = converter.process_links(
            html, links, headers_map, self.space_key, page_id, title
        )

        return html

    def add_cross_file_links(
        self,
        html: str,
        page_map: typing.Dict[str, dict],
    ) -> str:
        """
        Replace inter-document Markdown links with Confluence page URLs.

        When multiple Markdown files are published together, links like
        ``href="other-doc.md"`` or ``href="../docs/guide.md#section"`` are
        resolved against the current file's directory, looked up in
        *page_map*, and replaced with the published Confluence page URL.

        Links that do not resolve to a known page are left unchanged.

        Args:
            html: HTML string for the current page
            page_map: Mapping of *absolute file path* →
                      ``{"page_id": int, "title": str, "url": str}``

        Returns:
            modified HTML string
        """
        source_dir = os.path.dirname(os.path.abspath(self.file))

        # Match any <a href="..."> that looks like a relative .md path
        md_links = re.findall(
            r'<a href="((?![#"])(?:(?!\.md)[^"])*\.md(?:#[^"]*)?)">',
            html,
        )

        for raw_href in md_links:
            # Split off optional anchor fragment
            if "#" in raw_href:
                md_part, fragment = raw_href.split("#", 1)
            else:
                md_part, fragment = raw_href, ""

            # Resolve to absolute path
            abs_path = os.path.normpath(os.path.join(source_dir, md_part))

            entry = page_map.get(abs_path)
            if entry is None:
                LOGGER.debug(
                    "Cross-file link %s not found in page_map — skipping.", abs_path
                )
                continue

            base_url = entry["url"]
            if fragment:
                new_href = "%s#%s" % (base_url, fragment)
            else:
                new_href = base_url

            LOGGER.debug(
                "Replacing cross-file link %s → %s", raw_href, new_href
            )
            html = html.replace(
                'href="%s"' % raw_href,
                'href="%s"' % new_href,
            )

        return html

    def get_properties_to_update(self, props: dict, page_id: int) -> typing.List[any]:
        """
        Get a list of properties which have changed

        Args:
            page_id: integer
        Returns:
            array of properties to update
        """
        properties = self.confluence_client.get_page_properties(page_id)
        properties_for_update = []
        for existing_prop in properties:
            # Change the editor version
            if existing_prop["key"] == "editor" and existing_prop["value"] != (
                "v%d" % self.version
            ):
                properties_for_update.append(
                    {
                        "key": "editor",
                        "version": existing_prop["version"]["number"] + 1,
                        "value": ("v%d" % self.version),
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

    def get_confluence_api_url(self) -> str:
        url = ""
        if self.org_name is not None:
            if self.org_name.find(".") != -1:
                url = "https://%s" % self.org_name
            else:
                url = "https://%s.atlassian.net/wiki" % self.org_name
        if not self.use_ssl:
            url.replace("https://", "http://")
        return url

    def get_client(self) -> ConfluenceApiClient:
        url = self.get_confluence_api_url()

        return ConfluenceApiClient(
            url,
            self.user_name,
            self.api_key,
            self.space_key,
            self.version,
            self.use_ssl,
        )

    def get_space_key(self, space_key: str) -> str:
        if space_key is None:
            return "~%s" % (self.user_name)

        return space_key

    def get_parent_page(self):
        parent_page_id = 0
        if self.ancestor:
            LOGGER.debug("Resolving ancestor page/folder: %r", self.ancestor)
            parent_page = self.confluence_client.get_page(self.ancestor)
            if parent_page is not None and parent_page.id > 0:
                parent_page_id = parent_page.id
                LOGGER.debug(
                    "Ancestor resolved as page: id=%d, title=%r",
                    parent_page.id,
                    self.ancestor,
                )
            else:
                LOGGER.debug(
                    "Ancestor %r not found as a page; searching for a folder.", self.ancestor
                )
                parent_folder = self.confluence_client.get_folder(self.ancestor)
                if parent_folder > 0:
                    parent_page_id = parent_folder
                    LOGGER.debug(
                        "Ancestor resolved as folder: id=%d, title=%r",
                        parent_folder,
                        self.ancestor,
                    )

            if parent_page_id == 0:
                LOGGER.error(
                    "Error: Ancestor page/folder '%s' was not found in space '%s'.",
                    self.ancestor,
                    self.space_key,
                )
                LOGGER.error(
                    "Hint: check that --ancestor matches the exact page or folder "
                    "title in the target Confluence space."
                )
                sys.exit(1)

        return parent_page_id
