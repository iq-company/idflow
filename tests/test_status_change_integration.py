#!/usr/bin/env python3
"""
Integration tests for status change functionality.
Tests the complete workflow including CLI commands and their effects.
"""

import pytest
import tempfile
import shutil
import subprocess
import sys
import os
from pathlib import Path
from unittest.mock import patch


class TestStatusChangeIntegration:
    """Integration tests for status change functionality."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        test_data_dir = Path(temp_dir) / "test_data"
        test_data_dir.mkdir()

        # Create status directories
        for status in ["inbox", "active", "done", "blocked", "archived"]:
            (test_data_dir / status).mkdir()

        yield test_data_dir
        shutil.rmtree(temp_dir)

    def test_status_change_workflow(self, temp_workspace):
        """Test the complete status change workflow."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # Set environment variable for testing
        env = os.environ.copy()
        env['IDFLOW_BASE_DIR'] = str(test_data_dir)

        # Create a test document using the CLI
        result = subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'add',
            '--set', 'title=Status Test Document'
        ],
        input="This is a test document for status change testing.\n",
        text=True, capture_output=True, env=env, cwd=Path.cwd())

        assert result.returncode == 0, f"Add command failed: {result.stderr}"

        # Extract the document ID from output
        doc_id = result.stdout.strip()  # Now returns UUID directly
        assert doc_id, "Should have created a document with ID"

        # Verify document was created in inbox
        inbox_path = test_data_dir / "inbox" / doc_id
        assert inbox_path.exists(), "Document should be created in inbox"

        # Change status to active using CLI
        result = subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'set-status',
            doc_id, 'active'
        ],
        text=True, capture_output=True, env=env, cwd=Path.cwd())

        assert result.returncode == 0, f"Set-status command failed: {result.stderr}"
        assert "switched state" in result.stdout, "Should show status change message"

        # Verify directory was moved
        active_path = test_data_dir / "active" / doc_id
        assert active_path.exists(), "Document should now be in active"
        assert not inbox_path.exists(), "Document should no longer be in inbox"

        # Verify the doc.md file exists in the new location
        doc_file = active_path / "doc.md"
        assert doc_file.exists(), "doc.md should exist in new location"

        # Verify the content was updated
        content = doc_file.read_text()
        assert "status: active" in content, "Status should be updated in file"
        assert "title: Status Test Document" in content, "Title should be preserved"

        # Test locate command shows correct path
        result = subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'locate',
            doc_id
        ],
        text=True, capture_output=True, env=env, cwd=Path.cwd())

        assert result.returncode == 0, f"Locate command failed: {result.stderr}"
        assert "active" in result.stdout, "Locate should show active path"
        assert "inbox" not in result.stdout, "Locate should not show inbox path"

        # Test list command finds the document
        result = subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'list'
        ],
        text=True, capture_output=True, env=env, cwd=Path.cwd())

        assert result.returncode == 0, f"List command failed: {result.stderr}"
        assert doc_id in result.stdout, "List should show the document"

        # Test drop-all command deletes the document
        result = subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'drop-all',
            '--force'
        ],
        text=True, capture_output=True, env=env, cwd=Path.cwd())

        assert result.returncode == 0, f"Drop-all command failed: {result.stderr}"
        assert "deleted 1 docs" in result.stdout, "Should report 1 document deleted"

        # Verify document is gone
        assert not active_path.exists(), "Document should be deleted"

    def test_status_change_multiple_transitions(self, temp_workspace):
        """Test multiple status changes in sequence."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # Set environment variable for testing
        env = os.environ.copy()
        env['IDFLOW_BASE_DIR'] = str(test_data_dir)

        # Create a test document
        result = subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'add',
            '--set', 'title=Multi-Status Test'
        ],
        input="Testing multiple status changes.\n",
        text=True, capture_output=True, env=env, cwd=Path.cwd())

        assert result.returncode == 0, f"Add command failed: {result.stderr}"

        doc_id = result.stdout.strip()

        # inbox -> active
        result = subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'set-status',
            doc_id, 'active'
        ],
        text=True, capture_output=True, env=env, cwd=Path.cwd())

        assert result.returncode == 0, f"Status change to active failed: {result.stderr}"

        # Verify in active
        active_path = test_data_dir / "active" / doc_id
        assert active_path.exists(), "Document should be in active"

        # active -> done
        result = subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'set-status',
            doc_id, 'done'
        ],
        text=True, capture_output=True, env=env, cwd=Path.cwd())

        assert result.returncode == 0, f"Status change to done failed: {result.stderr}"

        # Verify in done
        done_path = test_data_dir / "done" / doc_id
        assert done_path.exists(), "Document should be in done"
        assert not active_path.exists(), "Document should no longer be in active"

        # Clean up
        subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'drop-all',
            '--force'
        ],
        text=True, capture_output=True, env=env, cwd=Path.cwd())

    def test_status_change_preserves_content(self, temp_workspace):
        """Test that status change preserves all document content."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # Set environment variable for testing
        env = os.environ.copy()
        env['IDFLOW_BASE_DIR'] = str(test_data_dir)

        # Create a test document with various properties
        result = subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'add',
            '--set', 'title=Content Test',
            '--set', 'priority=0.9',
            '--list-add', 'tags=important',
            '--list-add', 'tags=test'
        ],
        input="This document has various properties to test preservation.\n",
        text=True, capture_output=True, env=env, cwd=Path.cwd())

        assert result.returncode == 0, f"Add command failed: {result.stderr}"

        doc_id = result.stdout.strip()

        # Change status to active
        result = subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'set-status',
            doc_id, 'active'
        ],
        text=True, capture_output=True, env=env, cwd=Path.cwd())

        assert result.returncode == 0, f"Status change failed: {result.stderr}"

        # Verify content is preserved
        active_path = test_data_dir / "active" / doc_id
        doc_file = active_path / "doc.md"

        content = doc_file.read_text()
        assert "title: Content Test" in content, "Title should be preserved"
        assert "priority: '0.9'" in content, "Priority should be preserved"
        assert "tags:" in content, "Tags should be preserved"
        assert "important" in content, "Tag 'important' should be preserved"
        assert "test" in content, "Tag 'test' should be preserved"
        assert "This document has various properties" in content, "Body should be preserved"
        assert "status: active" in content, "Status should be updated"

        # Clean up
        subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'drop-all',
            '--force'
        ],
        text=True, capture_output=True, env=env, cwd=Path.cwd())

    def test_status_change_invalid_status(self, temp_workspace):
        """Test that invalid status changes are rejected."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # Set environment variable for testing
        env = os.environ.copy()
        env['IDFLOW_BASE_DIR'] = str(test_data_dir)

        # Create a test document
        result = subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'add',
            '--set', 'title=Invalid Status Test'
        ],
        input="Testing invalid status rejection.\n",
        text=True, capture_output=True, env=env, cwd=Path.cwd())

        assert result.returncode == 0, f"Add command failed: {result.stderr}"

        doc_id = result.stdout.strip()

        # Try to change to invalid status
        result = subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'set-status',
            doc_id, 'invalid_status'
        ],
        text=True, capture_output=True, env=env, cwd=Path.cwd())

        assert result.returncode != 0, "Should reject invalid status"
        assert "invalid" in result.stderr.lower() or "bad" in result.stderr.lower(), "Should show error message"

        # Clean up
        subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'drop-all',
            '--force'
        ],
        text=True, capture_output=True, env=env, cwd=Path.cwd())

    def test_status_change_nonexistent_document(self, temp_workspace):
        """Test that status change fails for nonexistent documents."""
        test_data_dir = Path(temp_workspace) / "test_data"

        # Set environment variable for testing
        env = os.environ.copy()
        env['IDFLOW_BASE_DIR'] = str(test_data_dir)

        # Try to change status of nonexistent document
        result = subprocess.run([
            sys.executable, '-m', 'idflow', 'doc', 'set-status',
            'nonexistent-uuid', 'active'
        ],
        text=True, capture_output=True, env=env, cwd=Path.cwd())

        assert result.returncode != 0, "Should fail for nonexistent document"
        assert "not found" in result.stderr.lower(), "Should show not found message"
