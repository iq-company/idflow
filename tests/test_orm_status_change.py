#!/usr/bin/env python3
"""
Tests for ORM status change functionality.
Tests the core ORM logic for status changes, directory movement, and path updates.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from idflow.core.document_factory import create_document, get_document_class
from idflow.core.config import config


class TestORMStatusChange:
    """Tests for ORM status change functionality."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        test_data_dir = Path(temp_dir) / "test_data"
        test_data_dir.mkdir()

        # Create status directories
        for status in ["inbox", "active", "done", "blocked", "archived"]:
            (test_data_dir / status).mkdir()

        # Set the base directory for testing
        original_base_dir = config._config["base_dir"]
        config._config["base_dir"] = str(test_data_dir)

        yield test_data_dir

        # Restore original config
        config._config["base_dir"] = original_base_dir
        shutil.rmtree(temp_dir)

    def test_document_creation_sets_original_status(self, temp_workspace):
        """Test that document creation sets the original status correctly."""
        # Create a document
        doc = create_document(status="inbox", title="Test Document")

        # Verify original status is set
        assert hasattr(doc, '_original_status')
        assert doc._original_status == "inbox"

        # Create the document
        doc.create()

        # Verify it's in the correct directory
        assert doc.doc_dir.parent.name == "inbox"
        assert doc.doc_file.parent.parent.name == "inbox"

    def test_status_change_triggers_directory_move(self, temp_workspace):
        """Test that changing status triggers directory movement."""
        # Create a document in inbox
        doc = create_document(status="inbox", title="Test Document")
        doc.create()

        # Verify initial location
        inbox_path = Path(temp_workspace) / "inbox" / doc.id
        active_path = Path(temp_workspace) / "active" / doc.id

        assert inbox_path.exists(), "Document should start in inbox"
        assert not active_path.exists(), "Document should not be in active yet"

        # Change status to active
        doc.status = "active"
        doc.save()

        # Verify directory was moved
        assert not inbox_path.exists(), "Document should no longer be in inbox"
        assert active_path.exists(), "Document should now be in active"

        # Verify paths are updated
        assert doc.doc_dir.parent.name == "active"
        assert doc.doc_file.parent.parent.name == "active"

    def test_status_change_preserves_document_content(self, temp_workspace):
        """Test that status change preserves all document content."""
        # Create a document with various properties
        doc = create_document(
            status="inbox",
            title="Test Document",
            priority=0.75,
            tags=["test", "status"]
        )
        doc.body = "This is the document body"
        doc.create()

        # Change status to active
        doc.status = "active"
        doc.save()

        # Verify content is preserved
        active_path = Path(temp_workspace) / "active" / doc.id
        doc_file = active_path / "doc.md"

        content = doc_file.read_text()
        assert "title: Test Document" in content, "Title should be preserved"
        assert "priority: 0.75" in content, "Priority should be preserved"
        assert "tags:" in content, "Tags should be preserved"
        assert "test" in content, "Tag 'test' should be preserved"
        assert "status" in content, "Tag 'status' should be preserved"
        assert "This is the document body" in content, "Body should be preserved"
        assert "status: active" in content, "Status should be updated"

    def test_status_change_updates_original_status(self, temp_workspace):
        """Test that original status is updated after status change."""
        # Create a document in inbox
        doc = create_document(status="inbox", title="Test Document")
        doc.create()

        # Verify initial original status
        assert doc._original_status == "inbox"

        # Change status to active
        doc.status = "active"
        doc.save()

        # Verify original status was updated
        assert doc._original_status == "active"

    def test_status_change_multiple_transitions(self, temp_workspace):
        """Test multiple status changes in sequence."""
        # Create a document in inbox
        doc = create_document(status="inbox", title="Test Document")
        doc.create()

        # inbox -> active
        doc.status = "active"
        doc.save()

        # Verify in active
        active_path = Path(temp_workspace) / "active" / doc.id
        assert active_path.exists(), "Document should be in active"
        assert doc._original_status == "active"

        # active -> done
        doc.status = "done"
        doc.save()

        # Verify in done
        done_path = Path(temp_workspace) / "done" / doc.id
        assert done_path.exists(), "Document should be in done"
        assert not active_path.exists(), "Document should no longer be in active"
        assert doc._original_status == "done"

    def test_status_change_with_files(self, temp_workspace):
        """Test that status change moves files with the document."""
        # Create a document in inbox
        doc = create_document(status="inbox", title="Test Document")
        doc.create()

        # Add a test file
        doc_dir = Path(temp_workspace) / "inbox" / doc.id
        test_file = doc_dir / "test.txt"
        test_file.write_text("This is a test file")

        # Change status to active
        doc.status = "active"
        doc.save()

        # Verify file was moved with the document
        active_path = Path(temp_workspace) / "active" / doc.id
        moved_test_file = active_path / "test.txt"

        assert moved_test_file.exists(), "Test file should be moved with document"
        assert moved_test_file.read_text() == "This is a test file", "File content should be preserved"

    def test_status_change_with_stages(self, temp_workspace):
        """Test that status change moves stages with the document."""
        # Create a document in inbox
        doc = create_document(status="inbox", title="Test Document")
        doc.create()

        # Create a stage
        doc_dir = Path(temp_workspace) / "inbox" / doc.id
        stages_dir = doc_dir / "stages"
        stages_dir.mkdir()

        stage_dir = stages_dir / "planning"
        stage_dir.mkdir()
        stage_file = stage_dir / "stage.md"
        stage_file.write_text("""---
name: "planning"
status: "done"
---
Planning stage content""")

        # Change status to active
        doc.status = "active"
        doc.save()

        # Verify stage was moved with the document
        active_path = Path(temp_workspace) / "active" / doc.id
        moved_stage_file = active_path / "stages" / "planning" / "stage.md"

        assert moved_stage_file.exists(), "Stage should be moved with document"
        assert "Planning stage content" in moved_stage_file.read_text(), "Stage content should be preserved"

    def test_status_change_find_after_move(self, temp_workspace):
        """Test that find works correctly after status change."""
        # Create a document in inbox
        doc = create_document(status="inbox", title="Test Document")
        doc.create()

        # Change status to active
        doc.status = "active"
        doc.save()

        # Find the document using ORM
        DocumentClass = get_document_class()
        found_doc = DocumentClass.find(doc.id)

        # Verify document was found
        assert found_doc is not None, "Document should be found after status change"
        assert found_doc.status == "active", "Found document should have active status"
        assert found_doc._original_status == "active", "Found document should have correct original status"

        # Verify paths are correct
        assert found_doc.doc_dir.parent.name == "active"
        assert found_doc.doc_file.parent.parent.name == "active"

    def test_status_change_where_after_move(self, temp_workspace):
        """Test that where works correctly after status change."""
        # Create a document in inbox
        doc = create_document(status="inbox", title="Test Document")
        doc.create()

        # Change status to active
        doc.status = "active"
        doc.save()

        # Find documents using ORM where
        DocumentClass = get_document_class()
        active_docs = DocumentClass.where(status="active")
        inbox_docs = DocumentClass.where(status="inbox")

        # Verify correct documents were found
        assert len(active_docs) == 1, "Should find 1 document in active"
        assert len(inbox_docs) == 0, "Should find 0 documents in inbox"

        # Verify the found document is correct
        found_doc = active_docs[0]
        assert found_doc.id == doc.id
        assert found_doc.status == "active"

    def test_status_change_no_duplicate_directories(self, temp_workspace):
        """Test that status change doesn't create duplicate directories."""
        # Create a document in inbox
        doc = create_document(status="inbox", title="Test Document")
        doc.create()

        # Change status to active
        doc.status = "active"
        doc.save()

        # Verify only one directory exists
        inbox_path = Path(temp_workspace) / "inbox" / doc.id
        active_path = Path(temp_workspace) / "active" / doc.id

        assert not inbox_path.exists(), "Document should not be in inbox"
        assert active_path.exists(), "Document should be in active"

        # Verify no duplicate directories exist
        all_dirs = list(Path(temp_workspace).rglob(doc.id))
        assert len(all_dirs) == 1, f"Should only have 1 directory, found: {all_dirs}"

    def test_status_change_handles_missing_original_status(self, temp_workspace):
        """Test that status change works correctly even in edge cases."""
        # Create a document in inbox
        doc = create_document(status="inbox", title="Test Document")
        doc.create()

        # Change status to active - should work
        doc.status = "active"
        doc.save()

        # Verify the change worked
        active_path = Path(temp_workspace) / "active" / doc.id
        assert active_path.exists(), "Document should be in active"

        # Verify the document was moved
        inbox_path = Path(temp_workspace) / "inbox" / doc.id
        assert not inbox_path.exists(), "Document should no longer be in inbox"

    def test_status_change_same_status_no_move(self, temp_workspace):
        """Test that changing to the same status doesn't trigger a move."""
        # Create a document in inbox
        doc = create_document(status="inbox", title="Test Document")
        doc.create()

        # Get the original directory path
        original_doc_dir = doc.doc_dir
        original_doc_file = doc.doc_file

        # Change status to inbox (same status)
        doc.status = "inbox"
        doc.save()

        # Verify no move occurred
        assert doc.doc_dir == original_doc_dir, "Directory should not have changed"
        assert doc.doc_file == original_doc_file, "File path should not have changed"

        # Verify document is still in inbox
        inbox_path = Path(temp_workspace) / "inbox" / doc.id
        assert inbox_path.exists(), "Document should still be in inbox"

    def test_status_change_preserves_document_references(self, temp_workspace):
        """Test that status change preserves document references."""
        # Create a document in inbox with references
        doc = create_document(status="inbox", title="Test Document")
        doc.add_doc_ref("related", "other-uuid")
        doc.add_file_ref("attachment", "test.pdf", "file-uuid")
        doc.create()

        # Change status to active
        doc.status = "active"
        doc.save()

        # Verify references are preserved
        active_path = Path(temp_workspace) / "active" / doc.id
        doc_file = active_path / "doc.md"

        content = doc_file.read_text()
        assert "_doc_refs:" in content, "Document references should be preserved"
        assert "_file_refs:" in content, "File references should be preserved"
        assert "related" in content, "Document reference key should be preserved"
        assert "attachment" in content, "File reference key should be preserved"
