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
            '<p><ac:structured-macro ac:name="toc" ac:schema-version="1"/></p>',
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
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+",
            flags=re.UNICODE,
        )
        return regrex_pattern.sub(r"", html)

    def convert_info_macros(self, html: str) -> str:
        """
        Converts html for info, note or warning macros

        Args:
            html: html string
        Returns:
            modified html string
        """
        info_tag = '<p><ac:structured-macro ac:name="info"><ac:rich-text-body><p>'
        note_tag = info_tag.replace("info", "note")
        warning_tag = info_tag.replace("info", "warning")
        close_tag = "</p></ac:rich-text-body></ac:structured-macro></p>"

        # Custom tags converted into macros
        html = html.replace("<p>~?", info_tag).replace("?~</p>", close_tag)
        html = html.replace("<p>~!", note_tag).replace("!~</p>", close_tag)
        html = html.replace("<p>~%", warning_tag).replace("%~</p>", close_tag)

        # Convert block quotes into macros
        quotes = re.findall("<blockquote>(.*?)</blockquote>", html, re.DOTALL)
        if quotes:
            for quote in quotes:
                note = re.search("^<.*>Note", quote.strip(), re.IGNORECASE)
                warning = re.search("^<.*>Warning", quote.strip(), re.IGNORECASE)

                if note:
                    clean_tag = self.strip_type(quote, "Note")
                    macro_tag = (
                        clean_tag.replace("<p>", note_tag)
                        .replace("</p>", close_tag)
                        .strip()
                    )
                elif warning:
                    clean_tag = self.strip_type(quote, "Warning")
                    macro_tag = (
                        clean_tag.replace("<p>", warning_tag)
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
        self, html, links, headers_map, space_id: int, page_id: int, title: str
    ):
        for link in links:
            matches = re.search(r'<a href="(#.+?)">(.+?)</a>', link)
            ref = matches.group(1)
            alt = matches.group(2)

            result_ref = headers_map.get(ref)

            if result_ref:
                base_uri = "%s/spaces/%d/pages/%d/%s" % (
                    self.api_url,
                    space_id,
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
