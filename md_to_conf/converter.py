import logging
import re
import codecs
import markdown
import typing

LOGGER = logging.getLogger(__name__)


class MarkdownConverter:
    """
    Wrapper for the `markdown` module that converts Markdown into HTML

    Provides some additional functions for advanced HTML processing

    """

    def __init__(self, md_file: str, api_url: str, md_source: str, editor_version: int):
        """
        Constructor

        Args:
            md_file: Path the the Markdown file
            api_url: Path the the Confluence API, used to build link urls
            md_source: MD Source format: current choices are `default` and `bitbucket`
            editor_version: Version to use for the editor
        """
        self.md_file = md_file
        self.api_url = api_url
        self.md_source = md_source
        self.editor_version = editor_version

    def convert_md_to_conf_html(
        self,
        has_title: bool = False,
        remove_emojies: bool = False,
        add_contents: bool = False,
    ):
        """
        Convert the Markdown file to Confluence HTML

        Args:
            has_title: Was a title provided via the CLI?
            remove_emojies: Should emojies be removed?
            add_contents: Should a contents section be added to the page

        Returns:
            A string representing HTML for the Markdown page
        """
        html = self.get_html_from_markdown()
        if not has_title:
            html = "\n".join(html.split("\n")[1:])

        LOGGER.debug("HTML pre processing")
        LOGGER.debug(html)
        html = self.create_table_of_content(html)
        html = self.convert_info_macros(html)
        html = self.convert_comment_block(html)
        html = self.convert_code_block(html)

        if remove_emojies:
            html = self.remove_emojies(html)

        if add_contents:
            html = self.add_contents(html)

        html = self.process_refs(html)
        return html

    def get_html_from_markdown(self) -> str:
        """
        Convert the Markdown file to HTML.  This is a wrapper
        around the markdown library

        Returns:
            A string representing HTML for the Markdown page
        """
        with codecs.open(self.md_file, "r", "utf-8") as mdfile:
            markdown_content = mdfile.read()
            html = markdown.markdown(
                markdown_content,
                extensions=[
                    "tables",
                    "fenced_code",
                    "footnotes",
                    "mdx_truly_sane_lists",
                ],
            )

        return html

    def convert_comment_block(self, html: str) -> str:
        """
        Convert markdown code bloc to Confluence hidden comment

        Args:
            html: string
        Returns:
            modified html string
        """
        open_tag = "<ac:placeholder>"
        close_tag = "</ac:placeholder>"
        html = html.replace("<!--", open_tag).replace("-->", close_tag)
        return html

    def create_table_of_content(self, html: str) -> str:
        """
        Check for the string '[TOC]' and replaces it the
        Confluence "Table of Content" macro

        Args:
            html: string
        Returns:
            modified html string
        """
        html = str.replace(
            html,
            r"<p>[TOC]</p>",
            '<p><ac:structured-macro ac:name="toc-zone" ac:schema-version="1" '
            'data-layout="default"><ac:rich-text-body><ac:structured-macro '
            'ac:name="toc" ac:schema-version="1" data-layout="default"/>'
            '</ac:rich-text-body></ac:structured-macro></p>',
        )

        return html

    def convert_code_block(self, html: str) -> str:
        """
        Convert html code blocks to Confluence macros

        Args:
            html: string
        Returns:
            modified html string
        """
        LOGGER.debug("HTML pre code block")
        LOGGER.debug(html)
        code_blocks = re.findall(r"<pre><code.*?>.*?</code></pre>", html, re.DOTALL)
        if code_blocks:
            for tag in code_blocks:
                conf_ml = '<ac:structured-macro ac:name="code">'
                conf_ml = (
                    conf_ml + '<ac:parameter ac:name="theme">Midnight</ac:parameter>'
                )
                conf_ml = (
                    conf_ml + '<ac:parameter ac:name="linenumbers">true</ac:parameter>'
                )

                lang = re.search('code class="language-(.*)"', tag)
                if lang:
                    lang = lang.group(1)
                else:
                    lang = "none"

                conf_ml = (
                    conf_ml
                    + '<ac:parameter ac:name="language">'
                    + lang
                    + "</ac:parameter>"
                )
                content = re.search(
                    r"<pre><code.*?>(.*?)</code></pre>", tag, re.DOTALL
                ).group(1)
                content = (
                    "<ac:plain-text-body><![CDATA["
                    + content
                    + "]]></ac:plain-text-body>"
                )
                conf_ml = conf_ml + content + "</ac:structured-macro>"
                conf_ml = conf_ml.replace("&lt;", "<").replace("&gt;", ">")
                conf_ml = conf_ml.replace("&quot;", '"').replace("&amp;", "&")

                html = html.replace(tag, conf_ml)

        return html

    def remove_emojies(self, html: str) -> str:
        """
        Remove emojies if there are any

        Args:
            html: string
        Returns:
            modified html string
        """
        regrex_pattern = re.compile(
            pattern="["
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f680-\U0001f6ff"  # transport & map symbols
            "\U0001f1e0-\U0001f1ff"  # flags (iOS)
            "]+",
            flags=re.UNICODE,
        )
        return regrex_pattern.sub(r"", html)

    def convert_github_alerts(self, html: str) -> str:
        """
        Convert GitHub-flavored markdown alert boxes to Confluence macros

        Supports GitHub alert syntax:
        > [!NOTE] Content
        > [!TIP] Content
        > [!IMPORTANT] Content
        > [!WARNING] Content
        > [!CAUTION] Content

        Args:
            html: html string
        Returns:
            modified html string with GitHub alerts converted to Confluence macros
        """
        # Find all blockquotes that might contain GitHub alerts
        blockquotes = re.findall(r"<blockquote>(.*?)</blockquote>", html, re.DOTALL)

        for quote in blockquotes:
            parsed_alert = self._parse_github_alert(quote)
            if parsed_alert:
                replacement_macro = self._create_alert_macro(parsed_alert)
                if replacement_macro:
                    html = html.replace(
                        f"<blockquote>{quote}</blockquote>", replacement_macro
                    )

        return html

    def _parse_github_alert(self, quote: str) -> typing.Optional[dict]:
        """
        Parse a blockquote to extract GitHub alert information.

        Args:
            quote: The blockquote content

        Returns:
            Dictionary with alert info if valid GitHub alert, None otherwise
        """
        if not quote.strip().startswith("<p>[!"):
            return None

        # Extract alert type
        alert_match = re.search(
            r"<p>\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", quote, re.IGNORECASE
        )
        if not alert_match:
            return None

        alert_type = alert_match.group(1).upper()

        # Find the content after the alert declaration
        content_start = alert_match.end()
        first_p_end = quote.find("</p>", content_start)

        if first_p_end == -1:
            return None

        # Extract first line content and remaining content
        first_line_content = quote[content_start:first_p_end].strip()
        remaining_content = quote[first_p_end + 4 :].strip()  # Skip '</p>'

        return {
            "alert_type": alert_type,
            "first_line_content": first_line_content,
            "remaining_content": remaining_content,
        }

    def _get_alert_macro_tags(self, alert_type: str) -> typing.Optional[tuple]:
        """
        Get the appropriate Confluence macro tags for the given alert type.

        Args:
            alert_type: The GitHub alert type (NOTE, TIP, etc.)

        Returns:
            Tuple of (opening_tag, closing_tag) or None if unknown type
        """
        # Define Confluence macro tags
        info_tag = '<p><ac:structured-macro ac:name="info"><ac:rich-text-body>'
        tip_tag = '<p><ac:structured-macro ac:name="tip"><ac:rich-text-body>'
        warning_tag = '<p><ac:structured-macro ac:name="note"><ac:rich-text-body>'
        error_tag = '<p><ac:structured-macro ac:name="warning"><ac:rich-text-body>'
        close_tag = "</ac:rich-text-body></ac:structured-macro></p>"

        # Special note tag for IMPORTANT alerts (using ADF panel format)
        note_tag = ('<ac:adf-extension><ac:adf-node type="panel">'
                    '<ac:adf-attribute key="panel-type">note</ac:adf-attribute>'
                    '<ac:adf-content>')
        note_close = "</ac:adf-content></ac:adf-node></ac:adf-extension>"

        alert_mapping = {
            "NOTE": (info_tag, close_tag),
            "TIP": (tip_tag, close_tag),
            "IMPORTANT": (note_tag, note_close),
            "WARNING": (warning_tag, close_tag),
            "CAUTION": (error_tag, close_tag),
        }

        return alert_mapping.get(alert_type)

    def _build_alert_content(
        self, first_line_content: str, remaining_content: str
    ) -> str:
        """
        Build the final content for the alert macro.

        Args:
            first_line_content: Content from the first line after alert declaration
            remaining_content: Any remaining content in the blockquote

        Returns:
            Formatted content string
        """
        content_parts = []
        if first_line_content:
            content_parts.append(f"<p>{first_line_content}</p>")
        if remaining_content:
            content_parts.append(remaining_content)

        final_content = "".join(content_parts)
        return final_content if final_content else "<p></p>"

    def _create_alert_macro(self, alert_info: dict) -> typing.Optional[str]:
        """
        Create a Confluence macro from parsed GitHub alert information.

        Args:
            alert_info: Dictionary containing alert type and content

        Returns:
            Confluence macro string or None if unknown alert type
        """
        macro_tags = self._get_alert_macro_tags(alert_info["alert_type"])
        if not macro_tags:
            return None  # Unknown alert type

        macro_tag, close_macro_tag = macro_tags
        final_content = self._build_alert_content(
            alert_info["first_line_content"], alert_info["remaining_content"]
        )

        return macro_tag + final_content + close_macro_tag

    def convert_info_macros(self, html: str) -> str:
        """
        Converts html for info, note or warning macros

        Args:
            html: html string
        Returns:
            modified html string
        """
        # First, convert GitHub-flavored markdown alerts (takes precedence)
        html = self.convert_github_alerts(html)

        info_tag = '<p><ac:structured-macro ac:name="info"><ac:rich-text-body><p>'
        # Warning (Yellow Caution Icon) is named 'note' in Confluence
        warning_tag = info_tag.replace("info", "note")
        # Success (Green Check Icon) is named 'tip' in Confluence
        success_tag = info_tag.replace("info", "tip")
        # Error (Red Cross Icon) is named 'warning' in Confluence
        error_tag = info_tag.replace("info", "warning")
        close_tag = "</p></ac:rich-text-body></ac:structured-macro></p>"

        note_tag = ('<ac:adf-extension><ac:adf-node type="panel">'
                    '<ac:adf-attribute key="panel-type">note</ac:adf-attribute>'
                    '<ac:adf-content><p>')
        note_close = '</p></ac:adf-content></ac:adf-node></ac:adf-extension>'

        # Custom tags converted into macros
        html = html.replace("<p>~?", info_tag).replace("?~</p>", close_tag)
        html = html.replace("<p>~%", warning_tag).replace("%~</p>", close_tag)
        html = html.replace("<p>~^", success_tag).replace("^~</p>", close_tag)
        html = html.replace("<p>~$", error_tag).replace("$~</p>", close_tag)

        html = html.replace("<p>~!", note_tag).replace("!~</p>", note_close)

        # Convert block quotes into macros
        quotes = re.findall("<blockquote>(.*?)</blockquote>", html, re.DOTALL)
        if quotes:
            for quote in quotes:
                note = re.search("^<.*>Note", quote.strip(), re.IGNORECASE)
                warning = re.search("^<.*>Warning", quote.strip(), re.IGNORECASE)
                success = re.search("^<.*>Success", quote.strip(), re.IGNORECASE)
                error = re.search("^<.*>Error", quote.strip(), re.IGNORECASE)

                if note:
                    clean_tag = self.strip_type(quote, "Note")
                    macro_tag = (
                        clean_tag.replace("<p>", note_tag)
                        .replace("</p>", note_close)
                        .strip()
                    )
                elif warning:
                    clean_tag = self.strip_type(quote, "Warning")
                    macro_tag = (
                        clean_tag.replace("<p>", warning_tag)
                        .replace("</p>", close_tag)
                        .strip()
                    )
                elif success:
                    clean_tag = self.strip_type(quote, "Success")
                    macro_tag = (
                        clean_tag.replace("<p>", success_tag)
                        .replace("</p>", close_tag)
                        .strip()
                    )
                elif error:
                    clean_tag = self.strip_type(quote, "Error")
                    macro_tag = (
                        clean_tag.replace("<p>", error_tag)
                        .replace("</p>", close_tag)
                        .strip()
                    )
                else:
                    macro_tag = (
                        quote.replace("<p>", info_tag)
                        .replace("</p>", close_tag)
                        .strip()
                    )

                html = html.replace("<blockquote>%s</blockquote>" % quote, macro_tag)

        # Convert doctoc to toc confluence macro
        html = self.convert_doctoc(html)

        return html

    def convert_doctoc(self, html: str) -> str:
        """
        Convert doctoc to confluence macro

        Args:
            html: html string
        Returns:
            modified html string
        """

        toc_tag = """<p>
        <ac:structured-macro ac:name="toc">
        <ac:parameter ac:name="printable">true</ac:parameter>
        <ac:parameter ac:name="style">disc</ac:parameter>
        <ac:parameter ac:name="maxLevel">7</ac:parameter>
        <ac:parameter ac:name="minLevel">1</ac:parameter>
        <ac:parameter ac:name="type">list</ac:parameter>
        <ac:parameter ac:name="outline">clear</ac:parameter>
        <ac:parameter ac:name="include">.*</ac:parameter>
        </ac:structured-macro>
        </p>"""

        html = re.sub(
            r"\<\!\-\- START doctoc.*END doctoc \-\-\>", toc_tag, html, flags=re.DOTALL
        )

        return html

    def strip_type(self, tag: str, tagtype: str) -> str:
        """
        Strips Note or Warning tags from html in various formats

        Args:
            tag: tag name
            tagtype: tag type
        Returns:
            modified tag
        """
        tag = re.sub(r"%s:\s" % tagtype, "", tag.strip(), re.IGNORECASE)
        tag = re.sub(r"%s\s:\s" % tagtype, "", tag.strip(), re.IGNORECASE)
        tag = re.sub(r"<.*?>%s:\s<.*?>" % tagtype, "", tag, re.IGNORECASE)
        tag = re.sub(r"<.*?>%s\s:\s<.*?>" % tagtype, "", tag, re.IGNORECASE)
        tag = re.sub(r"<(em|strong)>%s:<.*?>\s" % tagtype, "", tag, re.IGNORECASE)
        tag = re.sub(r"<(em|strong)>%s\s:<.*?>\s" % tagtype, "", tag, re.IGNORECASE)
        tag = re.sub(r"<(em|strong)>%s<.*?>:\s" % tagtype, "", tag, re.IGNORECASE)
        tag = re.sub(r"<(em|strong)>%s\s<.*?>:\s" % tagtype, "", tag, re.IGNORECASE)
        string_start = re.search("<[^>]*>", tag)
        tag = self.upper_chars(tag, [string_start.end()])
        return tag

    def upper_chars(self, string: str, indices: typing.List[int]) -> str:
        """
        Make characters uppercase in string

        Args:
            string: string to modify
            indices: character indice to change to uppercase
        Returns:
            uppercased string
        """
        upper_string = "".join(
            c.upper() if i in indices else c for i, c in enumerate(string)
        )
        return upper_string

    def slug(self, string: str, lowercase: bool) -> str:
        """
        Creates a slug string

        Args:
            string: string to modify
            lowercase: whether string has to be lowercased
        Returns:
            slug string
        """

        slug_string = string
        if lowercase:
            slug_string = string.lower()

        # Remove all html code tags
        slug_string = re.sub(r"<[^>]+>", "", slug_string)
        # Remove html code like '&amp;'
        slug_string = re.sub(r"&[a-z]+;", "", slug_string)
        # Replace all spaces ( ) with dash (-)
        slug_string = str.replace(slug_string, " ", "-")

        # Remove all special chars, except for dash (-)
        slug_string = re.sub(r"[^a-zA-Z0-9-]", "", slug_string)

        return slug_string

    def process_headers(self, ref_prefix, ref_postfix, headers):
        headers_map = {}
        headers_count = {}

        for header in headers:
            key = ref_prefix + self.slug(header, True)

            if self.editor_version == 1:
                value = re.sub(r"(<.+>| )", "", header)
            if self.editor_version == 2:
                value = self.slug(header, False)

            if key in headers_map:
                alt_count = headers_count[key]

                alt_key = key + (ref_postfix % alt_count)
                alt_value = value + (".%s" % alt_count)

                headers_map[alt_key] = alt_value
                headers_count[key] = alt_count + 1
            else:
                headers_map[key] = value
                headers_count[key] = 1

        return headers_map

    def process_links(
        self, html, links, headers_map, space_key: str, page_id: int, title: str
    ):
        for link in links:
            matches = re.search(r'<a href="(#.+?)">(.+?)</a>', link)
            ref = matches.group(1)
            alt = matches.group(2)

            result_ref = headers_map.get(ref)

            if result_ref:
                base_uri = "%s/spaces/%s/pages/%d/%s" % (
                    self.api_url,
                    space_key,
                    page_id,
                    "+".join(title.split()),
                )
                if self.editor_version == 1:
                    replacement = (
                        '<ac:link ac:anchor="%s">'
                        "<ac:plain-text-link-body>"
                        "<![CDATA[%s]]></ac:plain-text-link-body></ac:link>"
                        % (result_ref, re.sub(r"( *<.+> *)", " ", alt))
                    )
                if self.editor_version == 2:
                    replacement_uri = "%s#%s" % (base_uri, result_ref)
                    replacement = '<a href="%s" title="%s">%s</a>' % (
                        replacement_uri,
                        alt,
                        alt,
                    )

                LOGGER.debug("Replacing link %s with %s", link, replacement)
                html = html.replace(link, replacement)

        return html

    def process_refs(self, html: str) -> str:
        """
        Process references

        Args:
            html: html string
        Returns:
            modified html string
        """
        refs = re.findall(r"\n(\[\^(\d)\].*)|<p>(\[\^(\d)\].*)", html)

        if refs:
            for ref in refs:
                if ref[0]:
                    full_ref = ref[0].replace("</p>", "").replace("<p>", "")
                    ref_id = ref[1]
                else:
                    full_ref = ref[2]
                    ref_id = ref[3]

                full_ref = full_ref.replace("</p>", "").replace("<p>", "")
                html = html.replace(full_ref, "")
                href = re.search('href="(.*?)"', full_ref).group(1)

                superscript = '<a id="test" href="%s"><sup>%s</sup></a>' % (
                    href,
                    ref_id,
                )
                html = html.replace("[^%s]" % ref_id, superscript)

        return html

    # Scan for images and upload as attachments if found

    def add_contents(self, html: str) -> str:
        """
        Add contents page

        Args:
            html: html string
        Returns:
            modified html string
        """
        contents_markup = (
            '<ac:structured-macro ac:name="toc">\n<ac:parameter ac:name="printable">'
            'true</ac:parameter>\n<ac:parameter ac:name="style">disc</ac:parameter>'
        )
        contents_markup = (
            contents_markup + '<ac:parameter ac:name="maxLevel">5</ac:parameter>\n'
            '<ac:parameter ac:name="minLevel">1</ac:parameter>'
        )
        contents_markup = (
            contents_markup
            + '<ac:parameter ac:name="class">rm-contents</ac:parameter>\n'
            '<ac:parameter ac:name="exclude"></ac:parameter>\n'
            '<ac:parameter ac:name="type">list</ac:parameter>'
        )
        contents_markup = (
            contents_markup + '<ac:parameter ac:name="outline">false</ac:parameter>\n'
            '<ac:parameter ac:name="include"></ac:parameter>\n'
            "</ac:structured-macro>"
        )

        html = contents_markup + "\n" + html
        return html
