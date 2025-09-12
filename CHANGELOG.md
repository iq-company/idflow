# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- CLI interface with Typer
- Document management system
- Workflow engine integration
- AI-powered research capabilities
- Optional dependencies for research features
- PyPI publishing configuration
- GitHub Actions for automated publishing

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [0.1.0] - 2024-01-15

### Added
- Initial release
- Core document management functionality
- CLI commands for document operations
- Stage management system
- Worker framework
- Research tasks (gpt_researcher, duckduckgo_serp)
- Optional dependency management
- MIT License
- Comprehensive documentation

### Features
- Document creation, modification, and deletion
- Stage-based workflow processing
- AI-powered research automation
- Web scraping capabilities
- Keyword extraction
- LLM text completion
- Workflow management
- Worker process management

### Dependencies
- Core: typer, pydantic, PyYAML, conductor-python, litellm, keybert
- Research (optional): requests, playwright, beautifulsoup4, gpt-researcher
- Test (optional): pytest, pytest-cov
