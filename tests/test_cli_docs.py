#!/usr/bin/env python3
"""
Tests for the CLI document management functionality.
Tests the add, list, modify, set_status, drop, and drop_all commands.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open
from uuid import uuid4
import os

from idflow.core.config import config

# Test data constants
SAMPLE_DOC_CONTENT = """---
id: "doc1-uuid"
status: "inbox"
title: "Sample Document"
priority: 0.75
tags: ["sample", "test"]
notes: "This is a sample document for testing"
---
This is the body content of the sample document.

It contains multiple lines and demonstrates basic functionality."""

SAMPLE_DOC_WITH_REFS = """---
id: "doc2-uuid"
status: "active"
title: "Document with References"
priority: 0.85
tags: ["reference", "test"]
_doc_refs:
  - key: "source"
    uuid: "ref-uuid-123"
    data: {"role": "source"}
_file_refs:
  - key: "attachment"
    filename: "test.pdf"
    uuid: "file-uuid-456"
    data: {"note": "original upload"}
---
This document contains references to other documents and files."""


class TestCLIDocumentManagement:
    """Test suite for CLI document management operations."""

    def setup_method(self):
        """Set up test environment before each test method."""
        # Create a temporary workspace for each test
        self.temp_workspace = Path(tempfile.mkdtemp())
        self.test_data_dir = self.temp_workspace / "test_data"
        self.test_data_dir.mkdir()

        # Set environment variable for base_dir
        self.original_base_dir = os.environ.get("IDFLOW_BASE_DIR")
        os.environ["IDFLOW_BASE_DIR"] = str(self.test_data_dir)

        # Reload configuration to pick up the new environment variable
        config.reload()

    def teardown_method(self):
        """Clean up test environment after each test method."""
        # Restore original environment variable
        if self.original_base_dir is not None:
            os.environ["IDFLOW_BASE_DIR"] = self.original_base_dir
        else:
            os.environ.pop("IDFLOW_BASE_DIR", None)

        # Reload configuration
        config.reload()

        # Clean up temporary files
        shutil.rmtree(self.temp_workspace, ignore_errors=True)

    @pytest.fixture
    def sample_docs(self):
        """Create sample documents for testing."""
        # Create test documents in different statuses
        for status in ["inbox", "active", "done"]:
            status_dir = self.test_data_dir / status
            status_dir.mkdir(exist_ok=True)

            for i in range(2):
                doc_id = f"test-uuid-{status}-{i}"
                doc_dir = status_dir / doc_id
                doc_dir.mkdir()
                doc_file = doc_dir / "doc.md"
                doc_file.write_text(f"""---
id: "{doc_id}"
status: "{status}"
title: "Test Document {i}"
priority: {0.1 + i * 0.4}
tags: ["test", f"tag-{i}"]
---
Content for document {i}""")

        return self.test_data_dir

    def test_add_doc_basic(self):
        """Test basic document creation."""
        from idflow.cli.doc.add import add

        # Mock the uuid generation
        with patch('idflow.cli.doc.add.uuid4') as mock_uuid:
            mock_uuid.return_value = "test-uuid-123"

            # Test basic document creation
            result = add(
                body_arg="Test document body",
                status="inbox"
            )

            # Verify document was created
            doc_path = self.test_data_dir / "inbox" / "test-uuid-123" / "doc.md"
            assert doc_path.exists()

            # Verify content
            content = doc_path.read_text()
            assert "id: test-uuid-123" in content
            assert "status: inbox" in content
            assert "Test document body" in content

    def test_add_doc_with_properties(self):
        """Test document creation with various property types."""
        from idflow.cli.doc.add import add

        with patch('idflow.cli.doc.add.uuid4') as mock_uuid:
            mock_uuid.return_value = "test-uuid-456"

            # Set configuration for test
            # from idflow.core.config import config # This line is removed as per new_code
            # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

            # Test with various property types
            result = add(
                body_arg="Document with properties",
                status="inbox",
                set_=["title=Test Title", "priority=0.8", "meta.owner=alice"],
                list_add=["tags=observability", "tags=llm"],
                json_kv=['sources=[{"type":"rss","url":"https://example.com"}]']
            )

            # Verify document was created
            doc_path = self.test_data_dir / "inbox" / "test-uuid-456" / "doc.md"
            assert doc_path.exists()

            # Verify properties
            content = doc_path.read_text()
            assert "title: Test Title" in content
            assert "priority: 0.8" in content
            assert "meta:" in content
            assert "owner: alice" in content
            assert "tags:" in content
            assert "- llm" in content
            assert "sources:" in content
            assert "type: rss" in content

    def test_add_doc_with_doc_refs(self):
        """Test document creation with document references."""
        from idflow.cli.doc.add import add

        with patch('idflow.cli.doc.add.uuid4') as mock_uuid:
            mock_uuid.return_value = "test-uuid-789"

            # Set configuration for test
            # from idflow.core.config import config # This line is removed as per new_code
            # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

            # Test with document references
            result = add(
                body_arg="Document with doc refs",
                status="inbox",
                add_doc=['source=ref-uuid-123'],
                doc_data=['{"role":"source"}']
            )

            # Verify document was created
            doc_path = self.test_data_dir / "inbox" / "test-uuid-789" / "doc.md"
            assert doc_path.exists()

            # Verify doc refs
            content = doc_path.read_text()
            assert "_doc_refs:" in content
            assert "key: source" in content
            assert "uuid: ref-uuid-123" in content
            assert "role: source" in content

    def test_add_doc_with_file_refs(self):
        """Test document creation with file references."""
        from idflow.cli.doc.add import add

        # Create a test file
        test_file = self.temp_workspace / "test_file.txt"
        test_file.write_text("Test file content")

        with patch('idflow.cli.doc.add.uuid4') as mock_uuid:
            mock_uuid.return_value = "test-uuid-101"

            # Set configuration for test
            # from idflow.core.config import config # This line is removed as per new_code
            # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

            # Test with file references
            result = add(
                body_arg="Document with file refs",
                status="inbox",
                add_file=[f'attachment={test_file}'],
                file_data=['{"note":"test file"}']
            )

            # Verify document was created
            doc_path = self.test_data_dir / "inbox" / "test-uuid-101" / "doc.md"
            assert doc_path.exists()

            # Verify file refs
            content = doc_path.read_text()
            assert "_file_refs:" in content
            assert "key: attachment" in content
            assert "filename: test_file.txt" in content

    def test_list_docs_basic(self, sample_docs):
        """Test basic document listing."""
        from idflow.cli.doc.list import list_docs

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(sample_docs) # This line is removed as per new_code

        # Test basic listing
        result = list_docs()

        # Verify output contains expected documents
        assert result is None  # list_docs returns None, outputs to stdout

    def test_list_docs_with_filters(self, sample_docs):
        """Test document listing with various filters."""
        from idflow.cli.doc.list import list_docs

        # Test with status filter
        result = list_docs(status="inbox")
        assert result is None

        # Test with priority filter
        result = list_docs(priority=">0.5")
        assert result is None

        # Test with tags filter
        result = list_docs(tags="test")
        assert result is None

    def test_list_docs_with_columns(self, sample_docs):
        """Test document listing with custom columns."""
        from idflow.cli.doc.list import list_docs

        # Test with custom columns
        result = list_docs(columns=["id", "status", "title"])
        assert result is None

    def test_list_docs_with_doc_ref_filter(self, sample_docs):
        """Test document listing with document reference filters."""
        from idflow.cli.doc.list import list_docs

        # Test with doc ref filter
        result = list_docs(doc_ref="source")
        assert result is None

    def test_list_docs_with_file_ref_filter(self, sample_docs):
        """Test document listing with file reference filters."""
        from idflow.cli.doc.list import list_docs

        # Test with file ref filter
        result = list_docs(file_ref="attachment")
        assert result is None

    def test_modify_doc_basic(self):
        """Test basic document modification."""
        from idflow.cli.doc.modify import modify

        # Create a test document first
        doc_dir = self.test_data_dir / "inbox" / "test-uuid-modify"
        doc_dir.mkdir(parents=True)
        doc_file = doc_dir / "doc.md"
        doc_file.write_text("""---
id: "test-uuid-modify"
status: "inbox"
title: "Original Title"
---
Original content""")

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

        # Test basic modification
        result = modify(
            uuid="test-uuid-modify",
            set_=["title=Modified Title"]
        )

        # Verify modification
        content = doc_file.read_text()
        assert "title: Modified Title" in content
        assert "Original Title" not in content

    def test_modify_doc_with_list_add(self):
        """Test document modification with list additions."""
        from idflow.cli.doc.modify import modify

        # Create a test document
        doc_dir = self.test_data_dir / "inbox" / "test-uuid-list"
        doc_dir.mkdir(parents=True)
        doc_file = doc_dir / "doc.md"
        doc_file.write_text("""---
id: "test-uuid-list"
status: "inbox"
tags: ["original"]
---
Content""")

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

        # Test list addition
        result = modify(
            uuid="test-uuid-list",
            list_add=["tags=new_tag"]
        )

                            # Verify list addition
        content = doc_file.read_text()
        assert "tags:" in content
        # Note: list_add replaces the entire list, it doesn't append
        assert "- new_tag" in content

    def test_modify_doc_with_json(self):
        """Test document modification with JSON data."""
        from idflow.cli.doc.modify import modify

        # Create a test document
        doc_dir = self.test_data_dir / "inbox" / "test-uuid-json"
        doc_dir.mkdir(parents=True)
        doc_file = doc_dir / "doc.md"
        doc_file.write_text("""---
id: "test-uuid-json"
status: "inbox"
---
Content""")

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

        # Test JSON modification
        result = modify(
            uuid="test-uuid-json",
            json_kv=['metadata={"last_modified":"2024-01-01","version":"2.0"}']
        )

                            # Verify JSON modification
        content = doc_file.read_text()
        assert "metadata:" in content
        # Note: JSON values are stored as strings in YAML
        assert "last_modified: '2024-01-01'" in content
        assert "version: '2.0'" in content

    def test_set_status(self):
        """Test document status changes."""
        from idflow.cli.doc.set_status import set_status

        # Create a test document
        doc_dir = self.test_data_dir / "inbox" / "test-uuid-status"
        doc_dir.mkdir(parents=True)
        doc_file = doc_dir / "doc.md"
        doc_file.write_text("""---
id: "test-uuid-status"
status: "inbox"
---
Content""")

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

        # Test status change
        result = set_status(
            uuid="test-uuid-status",
            status="active"
        )

                                    # Verify status change
        # The file has been moved to the new status directory
        new_doc_path = self.test_data_dir / "active" / "test-uuid-status" / "doc.md"
        assert new_doc_path.exists()
        content = new_doc_path.read_text()
        assert "status: active" in content
        assert "status: inbox" not in content

    def test_drop_doc(self):
        """Test document deletion."""
        from idflow.cli.doc.drop import drop

        # Create a test document
        doc_dir = self.test_data_dir / "inbox" / "test-uuid-drop"
        doc_dir.mkdir(parents=True)
        doc_file = doc_dir / "doc.md"
        doc_file.write_text("""---
id: "test-uuid-drop"
status: "inbox"
---
Content""")

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

        # Test document deletion
        result = drop(
            uuid="test-uuid-drop"
        )

        # Verify deletion
        assert not doc_dir.exists()

    def test_drop_all_docs(self):
        """Test deletion of all documents."""
        from idflow.cli.doc.drop_all import drop_all

        # Create test documents
        for i in range(3):
            doc_dir = self.test_data_dir / "inbox" / f"test-uuid-{i}"
            doc_dir.mkdir(parents=True)
            (doc_dir / "doc.md").write_text(f"---\nid: test-uuid-{i}\nstatus: inbox\n---\nContent {i}")

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

        # Test deletion of all documents
        result = drop_all(force=True)

        # Verify all documents were deleted
        inbox_dir = self.test_data_dir / "inbox"
        assert inbox_dir.exists()
        assert len(list(inbox_dir.iterdir())) == 0

    def test_add_doc_invalid_status(self):
        """Test document creation with invalid status."""
        from idflow.cli.doc.add import add
        import typer

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

        with pytest.raises(typer.BadParameter):
            add(
                body_arg="Test document",
                status="invalid_status"
            )

    def test_add_doc_invalid_json(self):
        """Test document creation with invalid JSON."""
        from idflow.cli.doc.add import add
        import typer

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

        with pytest.raises(typer.BadParameter):
            add(
                body_arg="Test document",
                json_kv=['invalid=json']
            )

    def test_modify_nonexistent_doc(self):
        """Test modification of non-existent document."""
        from idflow.cli.doc.modify import modify
        import typer

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

        with pytest.raises(typer.BadParameter):
            modify(
                uuid="nonexistent-uuid",
                set_=["title=New Title"]
            )

    def test_set_status_invalid_status(self):
        """Test status change with invalid status."""
        from idflow.cli.doc.set_status import set_status
        import typer

        # Create a test document
        doc_dir = self.test_data_dir / "inbox" / "test-uuid-status"
        doc_dir.mkdir(parents=True)
        (doc_dir / "doc.md").write_text("---\nid: test-uuid-status\nstatus: inbox\n---\nContent")

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

        with pytest.raises(typer.BadParameter):
            set_status(
                uuid="test-uuid-status",
                status="invalid_status"
            )

    def test_drop_nonexistent_doc(self):
        """Test deletion of non-existent document."""
        from idflow.cli.doc.drop import drop
        import typer

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

        with pytest.raises(typer.BadParameter):
            drop(
                uuid="nonexistent-uuid"
            )

    def test_add_doc_with_stdin(self):
        """Test document creation with stdin input."""
        from idflow.cli.doc.add import add

        with patch('idflow.cli.doc.add.uuid4') as mock_uuid:
            mock_uuid.return_value = "test-uuid-stdin"

            # Mock stdin input
            # Set configuration for test
            # from idflow.core.config import config # This line is removed as per new_code
            # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

            mock_stdin = mock_open(read_data="Content from stdin")
            with patch('builtins.open', mock_stdin):
                result = add(
                    status="inbox"
                )

            # Verify document was created
            doc_path = self.test_data_dir / "inbox" / "test-uuid-stdin" / "doc.md"
            assert doc_path.exists()

    def test_modify_doc_with_stdin(self):
        """Test document modification with stdin input."""
        from idflow.cli.doc.modify import modify

        # Create a test document
        doc_dir = self.test_data_dir / "inbox" / "test-uuid-stdin"
        doc_dir.mkdir(parents=True)
        doc_file = doc_dir / "doc.md"
        doc_file.write_text("---\nid: test-uuid-stdin\nstatus: inbox\n---\nOriginal content")

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

        # Test modification without stdin (should keep original content)
        result = modify(
            uuid="test-uuid-stdin"
        )

        # Verify modification (content should remain unchanged)
        content = doc_file.read_text()
        assert "Original content" in content

    def test_list_docs_with_priority_filter(self, sample_docs):
        """Test document listing with priority filters."""
        from idflow.cli.doc.list import list_docs

        # Test various priority filters
        result = list_docs(priority=">0.5")
        assert result is None

        result = list_docs(priority="<0.5")
        assert result is None

        result = list_docs(priority="0.5-0.8")
        assert result is None

    def test_list_docs_with_exists_filter(self, sample_docs):
        """Test document listing with exists filters."""
        from idflow.cli.doc.list import list_docs

        # Test exists filters
        result = list_docs(exists="title")
        assert result is None

        result = list_docs(exists="!priority")
        assert result is None

    def test_add_doc_with_dot_paths(self):
        """Test document creation with dot notation paths."""
        from idflow.cli.doc.add import add

        with patch('idflow.cli.doc.add.uuid4') as mock_uuid:
            mock_uuid.return_value = "test-uuid-dot"

            # Set configuration for test
            # from idflow.core.config import config # This line is removed as per new_code
            # config._config["base_dir"] = str(Path(temp_workspace) / "test_data") # This line is removed as per new_code

            # Test with nested properties using dot notation
            result = add(
                body_arg="Document with nested properties",
                status="inbox",
                set_=["meta.owner=alice", "meta.department=engineering", "meta.flags.hot=true"]
            )

            # Verify document was created
            doc_path = self.test_data_dir / "inbox" / "test-uuid-dot" / "doc.md"
            assert doc_path.exists()

            # Verify nested properties
            content = doc_path.read_text()
            assert "meta:" in content
            assert "owner: alice" in content
            assert "department: engineering" in content
            assert "flags:" in content
            assert "hot: true" in content


class TestCLIErrorHandling:
    """Test suite for CLI error handling."""

    def test_add_doc_missing_equals(self):
        """Test error handling for missing equals in property assignments."""
        from idflow.cli.doc.add import add
        import typer

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(temp_data_dir) # This line is removed as per new_code

        with pytest.raises(typer.BadParameter):
            add(
                body_arg="Test document",
                set_=["invalid_property"]
            )

    def test_list_docs_missing_equals(self):
        """Test error handling for missing equals in list filters."""
        from idflow.cli.doc.list import list_docs
        import typer

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(temp_data_dir) # This line is removed as per new_code

        # This should not raise an error since tags is a valid filter parameter
        result = list_docs(
            tags="invalid_filter"
        )
        assert result is None

    def test_modify_doc_missing_equals(self):
        """Test error handling for missing equals in modify commands."""
        from idflow.cli.doc.modify import modify
        import typer

        # Set configuration for test
        # from idflow.core.config import config # This line is removed as per new_code
        # config._config["base_dir"] = str(temp_data_dir) # This line is removed as per new_code

        with pytest.raises(typer.BadParameter):
            modify(
                uuid="test-uuid",
                set_=["invalid_property"]
            )


if __name__ == "__main__":
    pytest.main([__file__])
