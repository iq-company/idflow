#!/usr/bin/env python3
"""
Pytest configuration and common fixtures for idflow tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch


@pytest.fixture(scope="session")
def test_workspace():
    """Create a test workspace for the entire test session."""
    temp_dir = tempfile.mkdtemp(prefix="idflow_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_data_dir(test_workspace):
    """Create a temporary data directory with status subdirectories."""
    test_data_dir = test_workspace / "test_data"
    test_data_dir.mkdir(exist_ok=True)

    # Create status directories
    for status in ["inbox", "active", "done", "blocked", "archived"]:
        (test_data_dir / status).mkdir(exist_ok=True)

    yield test_data_dir


@pytest.fixture
def mock_uuid():
    """Mock UUID generation for consistent testing."""
    with patch('uuid.uuid4') as mock:
        mock.return_value = "test-uuid-12345"
        yield mock


@pytest.fixture
def sample_document_content():
    """Sample document content for testing."""
    return """---
id: "test-uuid-123"
status: "inbox"
title: "Test Document"
priority: 0.75
tags: ["test", "example"]
notes: "This is a test document for testing purposes"
---
This is the body content of the test document.

It can contain multiple lines and paragraphs.

## Features
- Markdown support
- Frontmatter
- Multiple properties
- File references
- Document references"""


@pytest.fixture
def sample_document_with_refs():
    """Sample document with references for testing."""
    return """---
id: "test-uuid-456"
status: "active"
title: "Document with References"
priority: 0.85
tags: ["reference", "test"]
_doc_refs:
  - key: "research_source"
    uuid: "ref-uuid-789"
    data: {"role": "source", "priority": "high"}
  - key: "related_document"
    uuid: "ref-uuid-101"
    data: {"role": "reference", "type": "article"}
_file_refs:
  - key: "attachment"
    filename: "test.pdf"
    uuid: "file-uuid-202"
    data: {"note": "original upload", "category": "document"}
  - key: "image"
    filename: "diagram.png"
    uuid: "file-uuid-303"
    data: {"note": "process diagram", "category": "image"}
---
This document contains various references to other documents and files.

It demonstrates the full capability of the document reference system."""


@pytest.fixture
def complex_document_content():
    """Complex document with nested properties for testing."""
    return """---
id: "test-uuid-789"
status: "inbox"
title: "Complex Document Structure"
priority: 0.92
tags: ["complex", "nested", "test"]
meta:
  owner: "alice"
  department: "engineering"
  flags:
    hot: true
    urgent: false
    priority: "high"
  details:
    created: "2024-01-01"
    modified: "2024-01-15"
    version: "1.2.3"
    stages:
      - "draft"
      - "review"
      - "approved"
config:
  enabled: true
  timeout: 30
  retry_count: 3
  features:
    markdown: true
    frontmatter: true
    references: true
sources:
  - type: "rss"
    url: "https://example.com/feed"
    last_check: "2024-01-15T10:00:00Z"
  - type: "manual"
    author: "bob"
    date: "2024-01-14"
---
This is a complex document that tests all the property types and structures.

## Nested Properties
The document contains deeply nested properties to test the dot notation functionality.

## Lists and Dictionaries
Various data structures are included to ensure proper handling.

## References
Document and file references demonstrate the linking capabilities."""


@pytest.fixture
def test_files(test_workspace):
    """Create test files for file reference testing."""
    files = {}

    # Create various test files
    test_files = {
        "text": "test.txt",
        "pdf": "document.pdf",
        "image": "diagram.png",
        "config": "config.yml",
        "markdown": "notes.md"
    }

    for file_type, filename in test_files.items():
        file_path = test_workspace / filename
        if file_type == "text":
            file_path.write_text("This is a test text file.")
        elif file_type == "pdf":
            file_path.write_text("%PDF-1.4\nTest PDF content")
        elif file_type == "image":
            file_path.write_text("PNG\nTest image data")
        elif file_type == "config":
            file_path.write_text("config:\n  enabled: true\n  timeout: 30")
        elif file_type == "markdown":
            file_path.write_text("# Test Notes\n\nThese are test notes in markdown format.")

        files[file_type] = file_path

    yield files


@pytest.fixture
def mock_typer():
    """Mock typer functions for testing."""
    with patch('typer.echo') as mock_echo, \
         patch('typer.confirm') as mock_confirm, \
         patch('typer.prompt') as mock_prompt:

        # Set default return values
        mock_confirm.return_value = True
        mock_prompt.return_value = "1"

        yield {
            'echo': mock_echo,
            'confirm': mock_confirm,
            'prompt': mock_prompt
        }


@pytest.fixture
def mock_stdin(monkeypatch):
    """Mock stdin for testing."""
    mock_stdin = type('MockStdin', (), {
        'read': lambda: "Content from stdin",
        'isatty': lambda: False
    })()

    monkeypatch.setattr('sys.stdin', mock_stdin)
    return mock_stdin


# Test markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "cli: marks tests as CLI tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Mark CLI tests
        if "cli" in item.nodeid.lower():
            item.add_marker(pytest.mark.cli)

        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)

        # Mark unit tests (default for non-integration)
        if "integration" not in item.nodeid.lower():
            item.add_marker(pytest.mark.unit)
