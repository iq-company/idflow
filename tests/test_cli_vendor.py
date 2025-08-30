#!/usr/bin/env python3
"""
Tests for the vendor CLI functionality.
Tests the copy command for copying extendable functionality to local projects.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
import typer


class TestCLIVendor:
    """Test suite for vendor CLI commands."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.temp_project_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test environment after each test method."""
        if self.temp_project_dir.exists():
            shutil.rmtree(self.temp_project_dir)

    def test_copy_vendor_invalid_selection(self):
        """Test vendor copy with invalid user selection."""
        from idflow.cli.vendor.copy import copy_vendor
        import typer

        # Mock list_copyable to return valid options
        with patch('idflow.cli.vendor.copy.list_copyable') as mock_list:
            mock_list.return_value = [(1, "tasks", Path("/fake/path"))]

            # Mock invalid user input
            with patch('idflow.cli.vendor.copy.typer.prompt') as mock_prompt:
                mock_prompt.return_value = "99"  # Invalid selection

                with pytest.raises(typer.BadParameter):
                    copy_vendor(dest=self.temp_project_dir)

    def test_copy_vendor_no_options(self):
        """Test vendor copy when no options are available."""
        from idflow.cli.vendor.copy import copy_vendor
        import typer

        # Mock list_copyable to return empty list
        with patch('idflow.cli.vendor.copy.list_copyable') as mock_list:
            mock_list.return_value = []

            with pytest.raises(typer.Exit):
                copy_vendor(dest=self.temp_project_dir)

    def test_copy_vendor_parameter_extraction(self):
        """Test that typer parameters are extracted correctly."""
        from idflow.cli.vendor.copy import copy_vendor
        import typer

        # Test with typer.Option objects
        all_option = typer.Option(True, "--all")
        dest_option = typer.Option(self.temp_project_dir, "--dest")

        # Mock list_copyable to return empty list to trigger early exit
        with patch('idflow.cli.vendor.copy.list_copyable') as mock_list:
            mock_list.return_value = []

            with pytest.raises(typer.Exit):
                copy_vendor(all_=all_option, dest=dest_option)


class TestVendorCLIBasic:
    """Basic tests for vendor CLI functionality."""

    def test_import_vendor_module(self):
        """Test that vendor modules can be imported."""
        from idflow.cli.vendor import copy
        from idflow.core import vendor

        assert hasattr(copy, 'copy_vendor')
        assert hasattr(vendor, 'list_copyable')

    def test_vendor_core_functions(self):
        """Test core vendor functions."""
        from idflow.core.vendor import list_copyable, get_vendor_root

        # Test that functions return expected types
        vendor_root = get_vendor_root()
        assert isinstance(vendor_root, Path)

        copyable_items = list_copyable()
        assert isinstance(copyable_items, list)

        # Each item should be a tuple with 3 elements
        for item in copyable_items:
            assert isinstance(item, tuple)
            assert len(item) == 3
            assert isinstance(item[0], int)    # index
            assert isinstance(item[1], str)    # relative path
            assert isinstance(item[2], Path)   # absolute path
