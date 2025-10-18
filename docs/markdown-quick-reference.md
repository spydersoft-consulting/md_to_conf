# Markdown Quick Reference

Quick reference for special markdown syntax supported by md_to_conf converter.

## Status Panels

### GitHub-Flavored Markdown Alerts (Recommended)
```markdown
> [!NOTE]      # Info panel (blue icon)
> [!TIP]       # Tip panel (green icon)
> [!IMPORTANT] # Important panel (special ADF format)
> [!WARNING]   # Warning panel (yellow caution icon)
> [!CAUTION]   # Error panel (red cross icon)
```

### Blockquote Style
```markdown
> This is general info (blue icon)
> Warning: This is a warning (yellow caution icon)  
> Success: This is success (green check icon)
> Error: This is an error (red cross icon)
> Note: This is a note (special ADF format)
```

### Custom Tilde Style
```markdown
~?Info panel?~
~%Warning panel%~
~^Success panel^~
~$Error panel$~
~!Note panel!~
```

## Table of Contents

```markdown
[TOC]                           # Simple TOC
--add-contents flag             # Auto-add comprehensive TOC
<!-- START doctoc ... -->       # DocToc integration
```

## Code Blocks

````markdown
```javascript
// Language-specific code block
function example() { return true; }
```

```
// Generic code block (no language)
```
````

**Features:** Midnight theme, line numbers enabled, language detection

## Comments

```markdown
<!-- Hidden comment in Confluence -->
```

## Internal Links

```markdown
[Link to header](#header-name)           # Default format
[Link to header](#markdown-header-name)  # Bitbucket format
```

## Footnotes

```markdown
Text with footnote[^1].

[^1]: Footnote content with [link](url).
```

## Images

```markdown
![Alt text](local/image.png)     # Auto-uploaded as attachment
![Alt text](http://url/img.png)  # External URL preserved
```

## Special Options

- `--remove-emojies`: Remove all Unicode emojis
- `--add-contents`: Add comprehensive table of contents
- `--markdownsrc default|bitbucket`: Set anchor link format

## Standard Markdown

All standard markdown is supported:
- Headers: `# ## ### #### ##### ######`
- **Bold**, *italic*, ~~strikethrough~~, `inline code`
- Lists: `* - +` and `1. 2. 3.`
- Tables: `| col1 | col2 |`
- Links: `[text](url)`
- Images: `![alt](src)`

For complete documentation, see [markdown-syntax.md](markdown-syntax.md).