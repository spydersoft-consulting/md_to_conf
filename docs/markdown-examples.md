# Markdown Examples for md_to_conf

This file demonstrates all the markdown features supported by the md_to_conf converter.

## Standard Markdown Features

### Headers
# Header 1
## Header 2
### Header 3
#### Header 4
##### Header 5
###### Header 6

### Text Formatting
This is **bold text** and this is *italic text*.
You can also use ***bold and italic*** together.
~~Strikethrough~~ text is also supported.
Don't forget `inline code` formatting.

### Lists

#### Unordered Lists
* First item
* Second item
  * Nested item 2.1
  * Nested item 2.2
    * Deep nested item
* Third item

#### Ordered Lists
1. First numbered item
2. Second numbered item
   1. Nested numbered item 2.1
   2. Nested numbered item 2.2
      1. Deep nested numbered item
3. Third numbered item

### Tables
| Feature | Supported | Notes |
|---------|-----------|-------|
| Headers | ✓ | All 6 levels |
| Bold/Italic | ✓ | Standard markdown |
| Lists | ✓ | Including nested |
| Tables | ✓ | Full table support |
| Links | ✓ | Internal and external |

### Links and References
[External link](https://example.com)
[Link with title](https://example.com "Example Website")
[Internal link to header](#special-confluence-features)

## Special Confluence Features

### GitHub-Flavored Markdown Alerts (Recommended)

#### Note Alert (Info Panel)
> [!NOTE]
> This is a note alert that will appear in a blue info panel.

#### Tip Alert (Tip Panel)
> [!TIP]
> This is a tip alert that will appear in a green tip panel.

#### Important Alert (Special ADF Panel)
> [!IMPORTANT]
> This is an important alert that will appear in a special ADF note panel format for better visibility.

#### Warning Alert (Warning Panel)
> [!WARNING]
> This is a warning alert that will appear in a yellow warning panel.

#### Caution Alert (Error Panel)
> [!CAUTION]
> This is a caution alert that will appear in a red error panel.

### Status Panels via Blockquotes

#### Info Panel (Default)
> This is general information that will appear in a blue info panel.

#### Warning Panel
> Warning: This is a warning message that will appear in a yellow warning panel.

#### Success Panel
> Success: This is a success message that will appear in a green success panel.

#### Error Panel
> Error: This is an error message that will appear in a red error panel.

#### Note Panel
> Note: This is a note that will appear in a special note panel format.

### Custom Panel Syntax

#### Info Panel
~?This is an info panel using the custom tilde syntax.?~

#### Warning Panel
~%This is a warning panel using the custom tilde syntax.%~

#### Success Panel
~^This is a success panel using the custom tilde syntax.^~

#### Error Panel
~$This is an error panel using the custom tilde syntax.$~

#### Note Panel
~!This is a note panel using the custom tilde syntax.!~

## Table of Contents

### Simple TOC
[TOC]

### DocToc Example
<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Header 1](#header-1)
- [Header 2](#header-2)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Code Examples

### JavaScript Code Block
```javascript
function greetUser(name) {
    console.log(`Hello, ${name}!`);
    return true;
}

// Call the function
greetUser("World");
```

### Python Code Block
```python
def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

# Example usage
result = calculate_fibonacci(10)
print(f"The 10th Fibonacci number is: {result}")
```

### SQL Code Block
```sql
SELECT 
    users.name,
    users.email,
    COUNT(orders.id) as order_count
FROM users
LEFT JOIN orders ON users.id = orders.user_id
WHERE users.active = 1
GROUP BY users.id, users.name, users.email
ORDER BY order_count DESC;
```

### Generic Code Block (No Language)
```
This is a generic code block without a specific language.
It will still be formatted with the Midnight theme and line numbers.

function example() {
    return "No syntax highlighting";
}
```

## Comments and Hidden Content

### HTML Comments
<!-- This is a hidden comment that will be converted to a Confluence placeholder -->

These comments won't be visible in the final Confluence page but can be seen in the editor.

## Footnotes and References

This text has a footnote reference[^1].

Here's another reference to a different footnote[^2].

You can also reference the same footnote multiple times[^1].

[^1]: This is the first footnote with a [link to example.com](https://example.com).
[^2]: This is the second footnote with **bold text** and *italic text*.

## Images and Attachments

### Local Images (Auto-uploaded)
![Local diagram](./images/diagram.png)
![Screenshot with alt text](./screenshots/feature-demo.png "Demo Screenshot")

### External Images (URLs preserved)
![External image](https://via.placeholder.com/300x200/blue/white?text=External+Image)

## Advanced Internal Linking

This section demonstrates internal linking to other headers:

- Link to [Headers section](#headers)
- Link to [Code Examples](#code-examples)
- Link to [Status Panels](#status-panels-via-blockquotes)
- Link to [Table of Contents section](#table-of-contents)

## Emoji Examples

Here are some emojis that can be removed with the `--remove-emojies` option:

😀 😃 😄 😁 😆 😅 😂 🤣 😊 😇
🥰 😍 🤩 😘 😗 ☺️ 😚 😙 🥲 😋
👍 👎 👏 🙌 👐 🤲 🤝 🙏 ✍️ 💪
🚀 🛸 🌟 ⭐ 💫 ⚡ 🔥 💥 💨 💦
🇺🇸 🇬🇧 🇫🇷 🇩🇪 🇮🇹 🇪🇸 🇯🇵 🇨🇳 🇰🇷 🇮🇳

## Command Line Usage Examples

### Basic Conversion
```bash
md_to_conf example.md SPACEKEY -u username -p apikey -o orgname
```

### With Table of Contents
```bash
md_to_conf example.md SPACEKEY -u username -p apikey -o orgname --contents
```

### Remove Emojis and Add Custom Title
```bash
md_to_conf example.md SPACEKEY -u username -p apikey -o orgname \
  --remove-emojies --title "Custom Page Title"
```

### With Labels and Properties
```bash
md_to_conf example.md SPACEKEY -u username -p apikey -o orgname \
  --label "documentation" --label "markdown" \
  --property "team=engineering" --property "version=1.0"
```

### With Attachments
```bash
md_to_conf example.md SPACEKEY -u username -p apikey -o orgname \
  --attachment "diagrams/architecture.png" --attachment "files/config.json"
```

### Bitbucket Source Format
```bash
md_to_conf example.md SPACEKEY -u username -p apikey -o orgname \
  --markdownsrc bitbucket
```

### Simulation Mode (Preview Only)
```bash
md_to_conf example.md SPACEKEY -u username -p apikey -o orgname --simulate
```

## Processing Notes

### Order of Operations
1. Markdown → HTML conversion
2. Title processing
3. Table of contents generation
4. Panel/macro conversion
5. Comment processing
6. Code block formatting
7. Emoji removal (if enabled)
8. Contents addition (if enabled)
9. Reference processing
10. Internal link processing

### Limitations
- Internal links only work within the same page
- External image URLs are not uploaded as attachments
- Panel type detection requires specific keywords
- Nested list indentation must be consistent (2+ spaces)
- Code language detection depends on fence specification

This example file demonstrates all the supported markdown features. Copy sections as needed for your own documentation!