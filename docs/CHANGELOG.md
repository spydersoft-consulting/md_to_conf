# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

### Added

### Fixed

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
