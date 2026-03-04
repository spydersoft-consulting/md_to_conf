# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `--verbose` / `-V` flag — shorthand for `--loglevel DEBUG`; enables DEBUG-level logging across all modules (client, converter, confluence_converter)
- Debug-level logging for every API call: HTTP method, URL, and response status code are logged via `check_errors_and_get_json()`
- Debug-level parameter logging for `create_page()`, `update_page()`, `get_space_id()`, `get_page()`, and `get_folder()`
- `Title` field included in `log_not_found()` diagnostic output for page lookups
- Actionable hint messages for space-not-found and ancestor-not-found errors
- `Troubleshooting` section in getting-started documentation covering common failure modes with example error output

### Changed

- `log_not_found()` label for the API URL changed to "Confluence API URL" for clarity
- `-l` / `--loglevel` help text updated to list accepted values (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

### Fixed

- **`get_space_id()` fail-fast**: previously returned `-1` on a 404 or empty-results response, causing every subsequent API call to construct invalid URLs and emit cascading 404 errors. Now exits immediately with a clear error message and actionable hint.
- **`get_parent_page()` bug**: the "ancestor not found" error log was emitted even when `--ancestor` was not supplied (the guard was outside the `if self.ancestor:` block). When an ancestor is specified but cannot be found, the tool now exits immediately instead of silently continuing with `parent_page_id = 0`.
- Removed `404` from the HTTP retry `status_forcelist`. A 404 is not a transient network error; including it caused up to five redundant retries on every not-found response (e.g. wrong ancestor title), generating multiple misleading error messages.

## [1.2.1] - 2026-03-03

### Fixed

- `add_images()` no longer crashes when an `<img>` tag has no `alt` attribute — `alt_text` defaults to an empty string instead of raising `AttributeError`
- External images (URLs starting with `http`) are now skipped before attempting to upload, preventing unnecessary upload attempts for remote assets
- HTML src replacement for local images now always runs regardless of whether the image is external (previously the replacement was nested inside the `if not http` branch, so local image src paths could be left unrewritten in some edge cases)

### Added

- Comprehensive test coverage for `add_images()`: tests for local images, external URLs, images without alt text, and Confluence wiki-style URL rewriting
- Test image fixtures (`images/diagram.png`, `images/screenshot.jpg`, `simple.png`) for image upload tests

## [1.2.0] - 2026-02-27

### Added

- Mermaid diagram rendering via `--mermaid` flag — converts fenced `mermaid` code blocks to PNG images uploaded as Confluence attachments
- Two-strategy Mermaid rendering pipeline: local `mmdc` CLI (no network required) with automatic fallback to the `mermaid.ink` public API
- Multi-file processing — `markdownFile` argument now accepts multiple files and glob patterns (e.g. `docs/*.md`, `**/*.md`)
- `--exclude` flag for glob-based file exclusion; can be specified multiple times (`--exclude 'docs/draft*.md'`)
- Inline exclusion support via `!`-prefixed patterns in the file list (e.g. `!docs/draft.md`)
- Cross-file link resolution — relative `.md` links between co-published files are automatically rewritten to their Confluence page URLs
- `add_cross_file_links()` method in `ConfluenceConverter` for inter-document link resolution

### Fixed

- Regex patterns refactored to resolve SonarQube security issues

## [1.1.2] - 2025-10-20

### Fixed

- Attachment upload and download endpoints reverted to REST API v1 paths (`/rest/api/content/{id}/child/attachment/`) for compatibility

## [1.1.1] - 2025-10-18

### Changed

- Updated attachment handling to use Confluence REST API v2 endpoints consistently
- Improved error handling in get_attachment method with proper 404 response handling
- Enhanced attachment filename URL encoding for better compatibility
- Updated API client documentation and parameter descriptions

### Added

- Comprehensive test coverage for converter.py edge cases (code blocks without language, generic blockquotes)
- Additional test coverage for client.py error scenarios (delete page failures, attachment not found cases)
- Improved test infrastructure using proper mocking patterns with check_errors_and_get_json

### Fixed

- Attachment upload/download endpoints now properly use v2 API paths
- Better error logging and diagnostics for attachment operations

## [1.1.0] - 2025-10-18

### Added

- Support for GitHub-flavored markdown alert boxes ([!NOTE], [!TIP], [!IMPORTANT], [!WARNING], [!CAUTION])
- Comprehensive test coverage for GitHub alerts functionality
- Documentation for GitHub alerts in markdown syntax guide
- ADF panel format support for IMPORTANT alerts

### Changed

- Refactored GitHub alerts processing to reduce cognitive complexity
- Fixed ReDoS vulnerability in alert processing regex patterns
- Improved type annotations with Optional types for better code safety
- Updated documentation with GitHub alerts examples and usage

### Fixed

- Security vulnerability (SonarQube S5852) in regex patterns
- Type annotation warnings (SonarQube S5886) for functions returning None
- Code formatting and linting issues (flake8, black)

## [1.0.14] - 2025-10-17

### Added

- Folder ancestor support for page organization

## [1.0.13] - 2025-10-17

### Added

- Support for additional block types (Success and Error panels)
- Enhanced panel macro support with more visual indicators

### Changed

- Updated documentation with new block type examples
- Improved macro images in documentation

## [1.0.12] - 2025-10-17

### Fixed

- Link replacement functionality for better internal linking

## [1.0.11] - 2025-10-16

### Removed

- Unnecessary version metadata from editor processing

## [1.0.10] - 2025-10-01

### Changed

- Updated package requirements and dependencies

### Fixed

- GitHub Actions build process

## [1.0.9] - 2024-02-01

### Added

- Conversion functionality broken out into separate class for better modularity

### Fixed

- Issue with adding labels that do not exist yet
- Empty labels handling

### Changed

- GitHub Actions to build fix branches
- Code formatting improvements

## [1.0.8] - 2024-01-30

### Added

- Extension for proper list handling (mdx_truly_sane_lists)

### Fixed

- List conversion issues in markdown processing
- Missing requirement in setup.py

## [1.0.7] - 2024-01-29

### Fixed

- Organization name validation in API client

## [1.0.6] - 2024-01-29

### Fixed

- Module initialization and import issues
- SonarQube code quality issues
- Linting warnings and formatting

### Changed

- Updated GitHub Actions workflow steps
- Improved module structure

## [1.0.5] - 2023-08-14

### Added

- Change Log

## [1.0.4] - 2023-08-14

### Added

- Documentation via mkdocs, including a documentation publish pipeline

### Changed

- Added an `r` (raw) designation to Regex strings.
- Updated docstrings to Google style.

## [1.0.3] - 2023-08-11

### Changed

- Reverted Sonar suggestions to fix bug with TOC


## [1.0.2] - 2023-08-10

### Changed

- Reduced complexity on some functions
- Applied Black/Flake8 formatting across files


## [1.0.1] - 2023-08-10

### Changed

- Fixed PyPi packaging to properly version the published wheel

## [1.0.0] - 2023-08-10

### Changed

- Completed migration from RittmanMead/md_to_conf with packaging and PyPi publishing
