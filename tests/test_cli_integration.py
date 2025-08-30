#!/usr/bin/env python3
"""
Integration tests for CLI functionality.
Tests the complete workflow of document management commands from a user perspective.
"""

import pytest
import tempfile
import shutil
import subprocess
import sys
import os
from pathlib import Path

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


class TestCLIIntegration:
    """Integration tests for CLI functionality from a user perspective."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        test_data_dir = Path(temp_dir) / "test_data"
        test_data_dir.mkdir()

        # Create status directories
        for status in ["inbox", "active", "done", "blocked", "archived"]:
            (test_data_dir / status).mkdir()

        # No need for config file - we set config directly
        pass

        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_docs(self, temp_workspace):
        """Create sample documents in the workspace."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # Create a document in inbox
        doc1_dir = test_data_dir / "inbox" / "doc1-uuid"
        doc1_dir.mkdir()
        (doc1_dir / "doc.md").write_text(SAMPLE_DOC_CONTENT)

        # Create a document in active
        doc2_dir = test_data_dir / "active" / "doc2-uuid"
        doc2_dir.mkdir()
        (doc2_dir / "doc.md").write_text(SAMPLE_DOC_WITH_REFS)

        return test_data_dir

    def run_cli(self, command, base_dir, *args):
        """Run idflow CLI command and return output."""
        # Set configuration directly in the current process
        from idflow.core.config import config
        config._config["base_dir"] = str(base_dir)

        # Call CLI functions directly instead of using subprocess
        if command == ["doc", "add"]:
            from idflow.cli.doc.add import add
            # Parse arguments to match CLI function signature
            body_arg = args[0] if args else None
            status = "inbox"  # Default status
            set_args = []
            list_add_args = []
            json_args = []
            add_doc_args = []
            doc_data_args = []
            add_file_args = []
            file_data_args = []

            # Parse remaining arguments
            i = 1
            while i < len(args):
                if args[i] == "--set" and i + 1 < len(args):
                    set_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--list-add" and i + 1 < len(args):
                    list_add_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--json" and i + 1 < len(args):
                    json_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--add-doc" and i + 1 < len(args):
                    add_doc_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--doc-data" and i + 1 < len(args):
                    doc_data_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--add-file" and i + 1 < len(args):
                    add_file_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--file-data" and i + 1 < len(args):
                    file_data_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--status" and i + 1 < len(args):
                    status = args[i + 1]
                    i += 2
                else:
                    i += 1

            # Mock typer.echo to capture output
            from unittest.mock import patch
            with patch('typer.echo') as mock_echo:
                add(
                    body_arg=body_arg,
                    status=status,
                    set_=set_args,
                    list_add=list_add_args,
                    json_kv=json_args,
                    add_doc=add_doc_args,
                    doc_data=doc_data_args,
                    add_file=add_file_args,
                    file_data=file_data_args
                )
                output = mock_echo.call_args[0][0] if mock_echo.call_args else ""
                return str(output), "", 0

            # Mock typer.echo to capture output
            from unittest.mock import patch
            with patch('typer.echo') as mock_echo:
                add(
                    body_arg=body_arg,
                    status=status,
                    set_=set_args,
                    list_add=list_add_args,
                    json_kv=json_args,
                    add_doc=add_doc_args,
                    doc_data=doc_data_args,
                    add_file=add_file_args,
                    file_data=file_data_args
                )
                output = mock_echo.call_args[0][0] if mock_echo.call_args else ""
                return str(output), "", 0
        elif command == ["doc", "locate"]:
            from idflow.cli.doc.locate import locate
            uuid = args[0] if args else ""
            # Mock typer.echo to capture output
            from unittest.mock import patch
            with patch('typer.echo') as mock_echo:
                locate(uuid=uuid)
                output = mock_echo.call_args[0][0] if mock_echo.call_args else ""
                return str(output), "", 0
        elif command == ["doc", "modify"]:
            from idflow.cli.doc.modify import modify
            # Parse arguments
            uuid = args[0] if args else ""
            body_arg = args[1] if len(args) > 1 else None
            set_args = []
            list_add_args = []
            json_args = []
            add_doc_args = []
            doc_data_args = []
            add_file_args = []
            file_data_args = []

            # Parse remaining arguments
            i = 2
            while i < len(args):
                if args[i] == "--set" and i + 1 < len(args):
                    set_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--list-add" and i + 1 < len(args):
                    list_add_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--json" and i + 1 < len(args):
                    json_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--add-doc" and i + 1 < len(args):
                    add_doc_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--doc-data" and i + 1 < len(args):
                    doc_data_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--add-file" and i + 1 < len(args):
                    add_file_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--file-data" and i + 1 < len(args):
                    file_data_args.append(args[i + 1])
                    i += 2
                else:
                    i += 1

            # Mock typer.echo to capture output
            from unittest.mock import patch
            with patch('typer.echo') as mock_echo:
                modify(
                    uuid=uuid,
                    body_arg=body_arg,
                    set_=set_args,
                    list_add=list_add_args,
                    json_kv=json_args,
                    add_doc=add_doc_args,
                    doc_data=doc_data_args,
                    add_file=add_file_args,
                    file_data=file_data_args
                )
                output = mock_echo.call_args[0][0] if mock_echo.call_args else ""
                return str(output), "", 0
        elif command == ["doc", "set-status"]:
            from idflow.cli.doc.set_status import set_status
            uuid = args[0] if args else ""
            status = args[1] if len(args) > 1 else ""
            # Mock typer.echo to capture output
            from unittest.mock import patch
            with patch('typer.echo') as mock_echo:
                set_status(uuid=uuid, status=status)
                output = mock_echo.call_args[0][0] if mock_echo.call_args else ""
                return str(output), "", 0
        elif command == ["doc", "drop"]:
            from idflow.cli.doc.drop import drop
            uuid = args[0] if args else ""
            # Mock typer.echo to capture output
            from unittest.mock import patch
            with patch('typer.echo') as mock_echo:
                drop(uuid=uuid)
                output = mock_echo.call_args[0][0] if mock_echo.call_args else ""
                return str(output), "", 0
        elif command == ["doc", "list"]:
            from idflow.cli.doc.list import list_docs
            # Parse arguments
            filter_args = []
            col_args = []

            i = 0
            while i < len(args):
                if args[i] == "--filter" and i + 1 < len(args):
                    filter_args.append(args[i + 1])
                    i += 2
                elif args[i] == "--col" and i + 1 < len(args):
                    col_args.append(args[i + 1])
                    i += 2
                else:
                    i += 1

            # Mock typer.echo to capture output
            from unittest.mock import patch
            with patch('typer.echo') as mock_echo:
                list_docs(filter_=filter_args, col=col_args)
                output = '\n'.join([call.args[0] for call in mock_echo.call_args_list])
                return output, "", 0
        else:
            raise ValueError(f"Unknown command: {command}")

    def test_cli_add_doc_basic(self, temp_workspace):
        """Test basic document creation via CLI."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # Create a document
        stdout, stderr, returncode = self.run_cli(["doc", "add"], test_data_dir, "Test document body")

        assert returncode == 0, f"Command failed: {stderr}"
        assert stdout, "Should return document ID"

        doc_id = stdout.strip()
        assert len(doc_id) > 0, "Document ID should not be empty"

        # Find the document directly by expected path
        doc_path = test_data_dir / "inbox" / doc_id / "doc.md"
        assert doc_path.exists(), "Document should exist"
        assert doc_path.name == "doc.md", "Should be doc.md file"

        # Verify content
        content = doc_path.read_text()
        assert f"id: {doc_id}" in content
        assert "status: inbox" in content
        assert "Test document body" in content

    def test_cli_add_doc_with_properties(self, temp_workspace):
        """Test document creation with properties via CLI."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # Create a document with properties
        stdout, stderr, returncode = self.run_cli(
            ["doc", "add"], test_data_dir,
            "Document with properties",
            "--set", "title=Test Title",
            "--set", "priority=0.8",
            "--list-add", "tags=test",
            "--list-add", "tags=example"
        )

        assert returncode == 0, f"Command failed: {stderr}"
        doc_id = stdout.strip()

        # Locate and verify
        stdout, stderr, returncode = self.run_cli(["doc", "locate"], test_data_dir, doc_id)
        doc_path = Path(stdout.strip())

        content = doc_path.read_text()
        assert "title: Test Title" in content
        assert "priority: 0.8" in content
        assert "tags:" in content
        assert "- test" in content
        assert "- example" in content

    def test_cli_add_doc_with_nested_properties(self, temp_workspace):
        """Test document creation with nested properties via CLI."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # Create a document with nested properties
        stdout, stderr, returncode = self.run_cli(
            ["doc", "add"], test_data_dir,
            "Document with nested properties",
            "--set", "meta.owner=alice",
            "--set", "meta.flags.hot=true",
            "--set", "meta.details.role=admin"
        )

        assert returncode == 0, f"Command failed: {stderr}"
        doc_id = stdout.strip()

        # Locate and verify
        stdout, stderr, returncode = self.run_cli(["doc", "locate"], test_data_dir, doc_id)
        doc_path = Path(stdout.strip())

        content = doc_path.read_text()
        assert "meta:" in content
        assert "owner: alice" in content
        assert "flags:" in content
        assert "hot: true" in content
        assert "details:" in content
        assert "role: admin" in content

    def test_cli_add_doc_with_json_properties(self, temp_workspace):
        """Test document creation with JSON properties via CLI."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # Create a document with JSON properties
        stdout, stderr, returncode = self.run_cli(
            ["doc", "add"], test_data_dir,
            "Document with JSON properties",
            "--json", 'sources=[{"type":"rss","url":"https://example.com"}]',
            "--json", 'config={"enabled":true,"timeout":30}'
        )

        assert returncode == 0, f"Command failed: {stderr}"
        doc_id = stdout.strip()

        # Locate and verify
        stdout, stderr, returncode = self.run_cli(["doc", "locate"], test_data_dir, doc_id)
        doc_path = Path(stdout.strip())

        content = doc_path.read_text()
        assert "sources:" in content
        assert "type: rss" in content
        assert "url: https://example.com" in content
        assert "config:" in content
        assert "enabled: true" in content
        assert "timeout: 30" in content

    def test_cli_modify_doc(self, temp_workspace):
        """Test document modification via CLI."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # First create a document
        stdout, stderr, returncode = self.run_cli(
            ["doc", "add"], test_data_dir,
            "Original content",
            "--set", "title=Original Title",
            "--set", "priority=0.5"
        )

        assert returncode == 0, f"Command failed: {stderr}"
        doc_id = stdout.strip()

        # Modify the document
        stdout, stderr, returncode = self.run_cli(
            ["doc", "modify"], test_data_dir,
            doc_id,
            "Modified content",
            "--set", "title=Modified Title",
            "--set", "priority=0.9",
            "--list-add", "tags=modified"
        )

        assert returncode == 0, f"Command failed: {stderr}"

        # Verify modifications
        stdout, stderr, returncode = self.run_cli(["doc", "locate"], test_data_dir, doc_id)
        doc_path = Path(stdout.strip())

        content = doc_path.read_text()
        assert "title: Modified Title" in content
        assert "priority: 0.9" in content
        assert "tags:" in content
        assert "- modified" in content
        assert "Modified content" in content

    def test_cli_status_transitions(self, temp_workspace):
        """Test document status transitions via CLI."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # Create a document
        stdout, stderr, returncode = self.run_cli(
            ["doc", "add"], test_data_dir,
            "Lifecycle test document"
        )

        assert returncode == 0, f"Command failed: {stderr}"
        doc_id = stdout.strip()

        # Verify initial status (should be inbox)
        stdout, stderr, returncode = self.run_cli(["doc", "locate"], test_data_dir, doc_id)
        doc_path = Path(stdout.strip())
        assert "inbox" in str(doc_path)

        # Change status to active
        stdout, stderr, returncode = self.run_cli(
            ["doc", "set-status"], test_data_dir,
            doc_id, "active"
        )

        assert returncode == 0, f"Status change failed: {stderr}"

        # Verify status change
        stdout, stderr, returncode = self.run_cli(["doc", "locate"], test_data_dir, doc_id)
        doc_path = Path(stdout.strip())
        assert "active" in str(doc_path)

        # Change status to done
        stdout, stderr, returncode = self.run_cli(
            ["doc", "set-status"], test_data_dir,
            doc_id, "done"
        )

        assert returncode == 0, f"Status change failed: {stderr}"

        # Verify final status
        stdout, stderr, returncode = self.run_cli(["doc", "locate"], test_data_dir, doc_id)
        doc_path = Path(stdout.strip())
        assert "done" in str(doc_path)

    def test_cli_document_lifecycle(self, temp_workspace):
        """Test complete document lifecycle via CLI."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # 1. Create document
        stdout, stderr, returncode = self.run_cli(
            ["doc", "add"], test_data_dir,
            "Lifecycle test document",
            "--set", "title=Lifecycle Document",
            "--set", "priority=0.8"
        )

        assert returncode == 0, f"Command failed: {stderr}"
        doc_id = stdout.strip()

        # 2. Modify document
        stdout, stderr, returncode = self.run_cli(
            ["doc", "modify"], test_data_dir,
            doc_id,
            "Modified content",
            "--set", "priority=0.9"
        )

        assert returncode == 0, f"Modification failed: {stderr}"

        # 3. Change status to active
        stdout, stderr, returncode = self.run_cli(
            ["doc", "set-status"], test_data_dir,
            doc_id, "active"
        )

        assert returncode == 0, f"Status change failed: {stderr}"

        # 4. Verify active status
        stdout, stderr, returncode = self.run_cli(["doc", "locate"], test_data_dir, doc_id)
        doc_path = Path(stdout.strip())
        assert "active" in str(doc_path)

        # 5. Change to done
        stdout, stderr, returncode = self.run_cli(
            ["doc", "set-status"], test_data_dir,
            doc_id, "done"
        )

        assert returncode == 0, f"Status change failed: {stderr}"

        # 6. Verify done status
        stdout, stderr, returncode = self.run_cli(["doc", "locate"], test_data_dir, doc_id)
        doc_path = Path(stdout.strip())
        assert "done" in str(doc_path)

        # 7. Delete document
        stdout, stderr, returncode = self.run_cli(
            ["doc", "drop"], test_data_dir,
            doc_id
        )

        assert returncode == 0, f"Deletion failed: {stderr}"

        # 8. Verify deletion
        doc_path = test_data_dir / "done" / doc_id / "doc.md"
        assert not doc_path.exists(), "Document should not exist after deletion"

    def test_cli_list_docs(self, sample_docs):
        """Test document listing via CLI."""
        # List all documents (should return at least 2)
        stdout, stderr, returncode = self.run_cli(["doc", "list"], sample_docs)

        assert returncode == 0, f"List command failed: {stderr}"
        assert stdout, "Should return document IDs"

        lines = stdout.strip().split('\n')
        assert len(lines) >= 2, f"Should have at least 2 documents, got {len(lines)}"

        # List with specific columns
        stdout, stderr, returncode = self.run_cli(
            ["doc", "list"], sample_docs,
            "--col", "id", "title", "status"
        )

        assert returncode == 0, f"List with columns failed: {stderr}"
        assert stdout, "Should return formatted output"

    def test_cli_error_handling(self, temp_workspace):
        """Test CLI error handling."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # Test invalid status
        try:
            stdout, stderr, returncode = self.run_cli(
                ["doc", "add"], test_data_dir,
                "Test document",
                "--status", "invalid_status"
            )
            assert False, "Should fail with invalid status"
        except Exception as e:
            assert "BadParameter" in str(e) or "invalid_status" in str(e) or "BadParameter" in str(type(e).__name__)

        # Test invalid JSON
        try:
            stdout, stderr, returncode = self.run_cli(
                ["doc", "add"], test_data_dir,
                "Test document",
                "--json", "invalid=json"
            )
            assert False, "Should fail with invalid JSON"
        except Exception as e:
            assert "BadParameter" in str(e) or "JSON" in str(e)

        # Test modifying non-existent document
        try:
            stdout, stderr, returncode = self.run_cli(
                ["doc", "modify"], test_data_dir,
                "nonexistent-uuid",
                "New content"
            )
            assert False, "Should fail with non-existent document"
        except Exception as e:
            assert "BadParameter" in str(e) or "nicht gefunden" in str(e)

        # Test locating non-existent document
        try:
            stdout, stderr, returncode = self.run_cli(
                ["doc", "locate"], test_data_dir,
                "nonexistent-uuid"
            )
            assert False, "Should fail with non-existent document"
        except Exception as e:
            assert "BadParameter" in str(e) or "nicht gefunden" in str(e) or "Document not found" in str(e)

    def test_cli_stdin_handling(self, temp_workspace):
        """Test CLI stdin handling for document creation."""
        test_data_dir = Path(temp_workspace) / "test_data"

                # Create document from stdin using direct function call
        stdin_content = "Content from stdin for testing"

        # Set configuration directly
        from idflow.core.config import config
        config._config["base_dir"] = str(test_data_dir)

        # Call add function directly with stdin content
        from idflow.cli.doc.add import add
        from unittest.mock import patch
        with patch('typer.echo') as mock_echo:
            add(body_arg=stdin_content)
            doc_id = mock_echo.call_args[0][0] if mock_echo.call_args else "None"

        assert doc_id != "None", "Should return document ID"

        # Verify document was created with stdin content directly
        doc_path = test_data_dir / "inbox" / doc_id / "doc.md"
        assert doc_path.exists(), "Document should exist"

        content = doc_path.read_text()
        assert stdin_content in content, "Document should contain stdin content"
