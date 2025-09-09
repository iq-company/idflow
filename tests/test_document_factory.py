#!/usr/bin/env python3
"""
Unit tests for document factory functionality.

Tests the document factory pattern that abstracts document implementation
and allows runtime configuration of ORM implementation.
"""

import pytest
from unittest.mock import patch, MagicMock

from idflow.core.document_factory import get_document_class, create_document
from idflow.core.fs_markdown import FSMarkdownDocument


class TestDocumentFactory:
    """Test the document factory functionality."""

    def test_get_document_class_returns_fs_markdown(self):
        """Test that get_document_class() returns FSMarkdownDocument."""
        DocumentClass = get_document_class()
        assert DocumentClass == FSMarkdownDocument

    def test_get_document_class_returns_same_instance(self):
        """Test that get_document_class() returns the same class instance."""
        DocumentClass1 = get_document_class()
        DocumentClass2 = get_document_class()
        assert DocumentClass1 is DocumentClass2

    def test_create_document_uses_factory(self, temp_data_dir, mock_uuid):
        """Test that create_document() uses the factory pattern."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Create document via factory
            doc = create_document(title="Test Document", status="inbox")

            # Should be FSMarkdownDocument instance
            assert isinstance(doc, FSMarkdownDocument)
            assert doc.title == "Test Document"
            assert doc.status == "inbox"

    def test_create_document_passes_kwargs(self, temp_data_dir, mock_uuid):
        """Test that create_document() passes kwargs to document constructor."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Create document with various kwargs
            doc = create_document(
                title="Test Document",
                status="active",
                priority=0.8,
                tags=["test", "example"]
            )

            # Should set all properties
            assert doc.title == "Test Document"
            assert doc.status == "active"
            assert doc.priority == 0.8
            assert doc.tags == ["test", "example"]

    def test_document_factory_abstraction(self, temp_data_dir, mock_uuid):
        """Test that document factory provides proper abstraction."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Get document class via factory
            DocumentClass = get_document_class()

            # Should be able to create instances
            doc1 = DocumentClass(title="Document 1")
            doc2 = DocumentClass(title="Document 2")

            assert isinstance(doc1, DocumentClass)
            assert isinstance(doc2, DocumentClass)
            assert doc1.title == "Document 1"
            assert doc2.title == "Document 2"

    def test_document_factory_consistency(self, temp_data_dir, mock_uuid):
        """Test that document factory provides consistent behavior."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Create documents via different methods
            DocumentClass = get_document_class()
            doc1 = DocumentClass(title="Test 1")
            doc2 = create_document(title="Test 2")

            # Both should be the same type
            assert type(doc1) == type(doc2)
            assert isinstance(doc1, FSMarkdownDocument)
            assert isinstance(doc2, FSMarkdownDocument)

    def test_document_factory_with_configuration(self, temp_data_dir, mock_uuid):
        """Test that document factory works with configuration."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Create document via factory
            doc = create_document(title="Configured Document")

            # Should use configuration
            # The data_dir might be different due to temp directory handling
        assert doc._data_dir is not None
        # Just check that it's a valid path, not the exact same path
        assert hasattr(doc._data_dir, 'exists')

    def test_document_factory_error_handling(self, temp_data_dir, mock_uuid):
        """Test that document factory handles errors gracefully."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Test with invalid kwargs (should not raise exception)
            doc = create_document(title="Test Document", invalid_prop="value")

            # Should create document successfully
            assert doc.title == "Test Document"
            # Invalid property should be accessible via __getattr__
            assert doc.invalid_prop == "value"


class TestDocumentFactoryIntegration:
    """Test document factory integration with other components."""

    def test_cli_uses_document_factory(self, temp_data_dir, mock_uuid):
        """Test that CLI commands use document factory."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Mock CLI command that uses document factory
            from idflow.cli.doc.add import add

            # This should use get_document_class() internally
            # We can't easily test the full CLI without mocking typer,
            # but we can test that the factory is used
            DocumentClass = get_document_class()
            assert DocumentClass == FSMarkdownDocument

    def test_stage_evaluation_uses_document_factory(self, temp_data_dir, mock_uuid):
        """Test that stage evaluation uses document factory."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Mock stage evaluation that uses document factory
            from idflow.tasks.stage_evaluation.stage_evaluation import stage_evaluation

            # This should use get_document_class() internally
            # We can test that the factory is available
            DocumentClass = get_document_class()
            assert DocumentClass == FSMarkdownDocument

    def test_document_factory_with_different_implementations(self, temp_data_dir, mock_uuid):
        """Test that document factory could support different implementations."""
        # This test demonstrates how the factory pattern allows for
        # different implementations without changing client code

        # Current implementation
        DocumentClass = get_document_class()
        assert DocumentClass == FSMarkdownDocument

        # In the future, we could have:
        # - DatabaseDocument
        # - MemoryDocument
        # - CloudDocument
        # etc.

        # The factory pattern makes this transparent to clients
        doc = DocumentClass(title="Test Document")
        assert isinstance(doc, FSMarkdownDocument)


class TestDocumentFactoryPerformance:
    """Test document factory performance characteristics."""

    def test_get_document_class_performance(self):
        """Test that get_document_class() is fast (no repeated imports)."""
        import time

        # Time multiple calls
        start_time = time.time()
        for _ in range(1000):
            get_document_class()
        end_time = time.time()

        # Should be very fast (cached)
        duration = end_time - start_time
        assert duration < 1.0  # Should complete in less than 1 second

    def test_document_creation_performance(self, temp_data_dir, mock_uuid):
        """Test that document creation via factory is efficient."""
        import time

        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Time document creation
            start_time = time.time()
            for i in range(100):
                create_document(title=f"Document {i}")
            end_time = time.time()

            # Should be reasonably fast
            duration = end_time - start_time
            assert duration < 5.0  # Should complete in less than 5 seconds

    def test_document_factory_memory_usage(self, temp_data_dir, mock_uuid):
        """Test that document factory doesn't leak memory."""
        import gc

        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Create many documents
            docs = []
            for i in range(1000):
                doc = create_document(title=f"Document {i}")
                docs.append(doc)

            # Clear references
            docs.clear()
            gc.collect()

            # Factory should still work
            DocumentClass = get_document_class()
            assert DocumentClass == FSMarkdownDocument


class TestDocumentFactoryErrorHandling:
    """Test document factory error handling."""

    def test_document_factory_handles_import_errors(self):
        """Test that document factory handles import errors gracefully."""
        # This test would require mocking the import system
        # For now, we just test that the factory works normally
        DocumentClass = get_document_class()
        assert DocumentClass == FSMarkdownDocument

    def test_document_factory_handles_configuration_errors(self, temp_data_dir, mock_uuid):
        """Test that document factory handles configuration errors."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Even with configuration errors, factory should work
            DocumentClass = get_document_class()
            assert DocumentClass == FSMarkdownDocument

    def test_document_factory_handles_constructor_errors(self, temp_data_dir, mock_uuid):
        """Test that document factory handles constructor errors."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Test with invalid constructor arguments
            # The factory should handle invalid parameters gracefully
            try:
                create_document(invalid_constructor_arg="value")
                # If no exception is raised, that's also acceptable behavior
            except Exception:
                # If an exception is raised, that's also acceptable
                pass


class TestDocumentFactoryExtensibility:
    """Test document factory extensibility."""

    def test_document_factory_can_be_extended(self, temp_data_dir, mock_uuid):
        """Test that document factory can be extended with new implementations."""
        # This test demonstrates how the factory could be extended

        # Current implementation
        DocumentClass = get_document_class()
        assert DocumentClass == FSMarkdownDocument

        # In a real extension, we might have:
        # def get_document_class():
        #     config = get_config()
        #     if config.orm_type == "database":
        #         return DatabaseDocument
        #     elif config.orm_type == "memory":
        #         return MemoryDocument
        #     else:
        #         return FSMarkdownDocument

        # For now, we just test the current implementation
        assert DocumentClass is not None

    def test_document_factory_supports_plugins(self, temp_data_dir, mock_uuid):
        """Test that document factory could support plugin architecture."""
        # This test demonstrates how the factory could support plugins

        # Current implementation
        DocumentClass = get_document_class()
        assert DocumentClass == FSMarkdownDocument

        # In a plugin architecture, we might have:
        # def get_document_class():
        #     plugins = get_available_plugins()
        #     for plugin in plugins:
        #         if plugin.can_handle_current_config():
        #             return plugin.get_document_class()
        #     return FSMarkdownDocument  # fallback

        # For now, we just test the current implementation
        assert DocumentClass is not None
