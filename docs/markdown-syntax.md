# Markdown Syntax Guide

This document describes the standard and special markdown syntax supported by the md_to_conf converter. The converter transforms markdown files into Confluence-compatible HTML using the Python `markdown` library with additional custom processing.

## Table of Contents

- [Standard Markdown Support](#standard-markdown-support)
- [Special Confluence Features](#special-confluence-features)
- [Custom Panel Syntax](#custom-panel-syntax)
- [Table of Contents Generation](#table-of-contents-generation)
- [Code Blocks](#code-blocks)
- [Comments](#comments)
- [References and Footnotes](#references-and-footnotes)
- [Internal Links](#internal-links)
- [Images and Attachments](#images-and-attachments)
- [Emoji Support](#emoji-support)

## Standard Markdown Support

The converter supports all standard markdown syntax through the Python `markdown` library with the following extensions enabled:

### Headers

```markdown
# Header 1
## Header 2  
### Header 3
#### Header 4
##### Header 5
###### Header 6
```

Headers are converted to Confluence headings and can be used as anchor targets for internal links.

### Text Formatting

```markdown
**Bold text**
*Italic text*
***Bold and italic***
~~Strikethrough~~
`Inline code`
```

### Lists

#### Unordered Lists
```markdown
* Item 1
* Item 2
  * Nested item 2.1
  * Nested item 2.2
* Item 3
```

#### Ordered Lists
```markdown
1. First item
2. Second item
   1. Nested item 2.1
   2. Nested item 2.2
3. Third item
```

The converter uses the `mdx_truly_sane_lists` extension for proper nested list handling.

### Tables

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1    | Data     | Data     |
| Row 2    | Data     | Data     |
```

Tables are supported through the `tables` extension and converted to Confluence table format.

### Links

```markdown
[Link text](https://example.com)
[Link with title](https://example.com "Title")
```

### Blockquotes

```markdown
> This is a blockquote
> 
> Multiple lines are supported
```

See [Special Confluence Features](#special-confluence-features) for enhanced blockquote functionality.

## Special Confluence Features

### Enhanced Blockquotes with Status Panels

The converter automatically detects special blockquote patterns and converts them to Confluence status panels:

#### Info Panel (Blue Icon)
```markdown
> This is general information.
```

#### Warning Panel (Yellow Caution Icon)
```markdown
> Warning: This is a warning message.
```

#### Success Panel (Green Check Icon)
```markdown
> Success: This is a success message.
```

#### Error Panel (Red Cross Icon)
```markdown
> Error: This is an error message.
```

#### Note Panel (Special ADF Format)
```markdown
> Note: This is a note.
```

**Note:** The type detection is case-insensitive and supports various formats like "Warning:", "Warning :", etc.

## Custom Panel Syntax

For more explicit control over panel types, use the custom tilde syntax:

### Info Panel
```markdown
~?This is an info panel.?~
```

### Warning Panel
```markdown
~%This is a warning panel.%~
```

### Success Panel
```markdown
~^This is a success panel.^~
```

### Error Panel
```markdown
~$This is an error panel.$~
```

### Note Panel
```markdown
~!This is a note panel.!~
```

## Table of Contents Generation

### Simple TOC
```markdown
[TOC]
```

This creates a basic table of contents macro in Confluence.

### DocToc Integration
```markdown
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
<!-- END doctoc generated TOC please keep comment here to allow auto update -->
```

The converter automatically replaces doctoc-generated sections with Confluence TOC macros with advanced parameters:
- Printable: true
- Style: disc
- Max Level: 7
- Min Level: 1
- Type: list
- Outline: clear

### Contents Addition
When using the `--add-contents` option, a comprehensive table of contents is automatically added to the beginning of the page with these parameters:
- Printable: true
- Style: disc
- Max Level: 5
- Min Level: 1
- Class: rm-contents
- Type: list
- Outline: false

## Code Blocks

### Fenced Code Blocks
````markdown
```javascript
function example() {
    return "Hello, World!";
}
```
````

### Code Block without Language
````markdown
```
This is a generic code block
```
````

**Features:**
- All code blocks are converted to Confluence code macros
- Theme: Midnight (dark theme)
- Line numbers: enabled
- Language detection from fence language specification
- Falls back to "none" if no language specified
- HTML entities are properly unescaped

**Supported Languages:** Any language supported by Confluence code macros (JavaScript, Python, Java, SQL, etc.)

## Comments

### HTML Comments
```markdown
<!-- This is a hidden comment -->
```

HTML comments are converted to Confluence placeholder macros (`<ac:placeholder>`) which render as hidden comments in Confluence.

## References and Footnotes

### Footnote References
```markdown
Here is some text with a footnote reference[^1].

[^1]: This is the footnote content with a [link](https://example.com).
```

**Features:**
- Footnotes are supported through the `footnotes` extension
- References are converted to superscript links
- Footnote content is processed and linked appropriately

## Internal Links

### Header Anchor Links
```markdown
[Link to section](#header-name)
```

**Features:**
- Links to headers within the same page are automatically converted
- Supports both `default` and `bitbucket` markdown source formats
- Different anchor prefixes based on source:
  - Default: `#`
  - Bitbucket: `#markdown-header-`
- Proper URL encoding for Confluence page URLs
- Different output formats for editor versions 1 and 2

### Supported Markdown Sources

#### Default Format
```markdown
[Link to header](#my-header)
```

#### Bitbucket Format
```markdown
[Link to header](#markdown-header-my-header)
```

## Images and Attachments

### Image Syntax
```markdown
![Alt text](path/to/image.png)
![Alt text with title](path/to/image.png "Image title")
```

**Features:**
- Local images are automatically uploaded as Confluence attachments
- Image paths are converted to Confluence attachment URLs
- HTTP/HTTPS URLs are left unchanged
- Alt text is preserved in the attachment metadata

**Automatic Processing:**
- Local file paths are resolved relative to the markdown file location
- Images are uploaded to the target Confluence page
- Image references are updated to point to Confluence attachment URLs
- Format: `/wiki/download/attachments/{page_id}/{filename}` or `/download/attachments/{page_id}/{filename}`

## Emoji Support

### Emoji Removal
When using the `--remove-emojies` option, the converter removes Unicode emoji characters:

**Removed Emoji Ranges:**
- Emoticons: `\U0001F600-\U0001F64F`
- Symbols & Pictographs: `\U0001F300-\U0001F5FF`  
- Transport & Map Symbols: `\U0001F680-\U0001F6FF`
- Flags (iOS): `\U0001F1E0-\U0001F1FF`

**Example:**
```markdown
This text has emojis 😀 🎉 🚀 🇺🇸
```

With `--remove-emojies`, becomes:
```
This text has emojis
```

## Advanced Features

### Command Line Options

The converter supports several command-line options that affect markdown processing:

#### Content Options
- `--contents` / `-c`: Generate a comprehensive table of contents at the beginning of the page
- `--title`: Set a custom page title (otherwise uses first line of markdown file)
- `--remove-emojies`: Remove all Unicode emojis from the content

#### Markdown Source Format
- `--markdownsrc` / `-mds`: Specify markdown source format
  - `default`: Standard markdown anchor format (`#header-name`)
  - `bitbucket`: Bitbucket-style anchors (`#markdown-header-header-name`)

#### Page Management
- `--label`: Add labels to the Confluence page (can be used multiple times)
- `--property`: Set content properties on the page (format: `key=value`, can be used multiple times)
- `--attachment` / `-t`: Upload file attachments to the page (paths relative to markdown file)

#### Processing Options
- `--version` / `-v`: Confluence editor version (1 or 2, default: 2)
- `--simulate` / `-s`: Show conversion result without uploading to Confluence
- `--delete` / `-d`: Delete the page instead of creating/updating it

### Editor Version Support

The converter supports two editor versions with different output formats:

#### Editor Version 1 (Legacy)
- Uses Confluence-specific XML link format
- Internal links: `<ac:link ac:anchor="..."><ac:plain-text-link-body><![CDATA[...]]></ac:plain-text-link-body></ac:link>`

#### Editor Version 2 (Modern)
- Uses standard HTML anchor links
- Internal links: `<a href="...#..." title="...">...</a>`
- Full Confluence page URLs with anchor fragments

### Markdown Source Formats

#### Default Source
- Standard markdown anchor format: `#header-name`
- Postfix pattern for duplicates: `_%d`

#### Bitbucket Source  
- Bitbucket-style anchors: `#markdown-header-header-name`
- Postfix pattern for duplicates: `_%d`

### Processing Order

The converter processes markdown in this order:
1. Convert markdown to HTML using Python `markdown` library
2. Remove title if not explicitly provided
3. Process table of contents markers
4. Convert info/warning/success/error macros
5. Convert HTML comments to placeholders
6. Convert code blocks to Confluence macros
7. Remove emojis (if requested)
8. Add contents section (if requested)
9. Process footnote references
10. Process internal anchor links

## Limitations and Notes

1. **Internal Links**: Only work within the same page. Cross-page links are not automatically converted.

2. **Image Processing**: Only local images are uploaded as attachments. External URLs are preserved as-is.

3. **Code Language Detection**: Language detection relies on the fence specification. Unknown languages default to "none".

4. **Panel Type Detection**: Blockquote panel type detection is case-insensitive but requires specific keywords (Warning, Success, Error, Note).

5. **Anchor Generation**: Anchor names are automatically generated from header text with special character removal and space-to-dash conversion.

6. **Nested Lists**: Proper indentation is required for nested list items (2+ spaces for sub-items).

7. **Emoji Removal**: When enabled, removes all emojis indiscriminately - cannot selectively preserve certain emojis.

## Examples

For complete examples, see the test files:
- `tests/testfiles/basic.md` - Basic markdown features
- `tests/testfiles/advanced.md` - Advanced features including panels, nested lists, and internal links