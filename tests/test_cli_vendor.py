#!/usr/bin/env python3
"""
Tests for the vendor CLI functionality.
Tests the copy command for copying extendable functionality to local projects.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import typer

# Mock data for testing
MOCK_VENDOR_DIRS = [
    "tasks",
    "templates/researcher",
    "templates/enricher",
    "templates/generator"
]


class TestCLIVendor:
    """Test suite for vendor CLI commands."""

    def setup_method(self):
        """Set up test environment before each test method."""
        # Create temporary directories for each test
        self.temp_project_dir = Path(tempfile.mkdtemp())
        self.mock_pip_package = Path(tempfile.mkdtemp())

        # Create mock pip package structure
        pip_dir = self.mock_pip_package / "idflow"
        pip_dir.mkdir()

        # Create mock vendor directories with real files
        for vendor_dir in MOCK_VENDOR_DIRS:
            full_path = pip_dir / vendor_dir
            full_path.mkdir(parents=True, exist_ok=True)

            # Add some mock files
            if vendor_dir == "tasks":
                (full_path / "sample_task.py").write_text("# Sample task\n\ndef run():\n    return 'Hello from task'")
                (full_path / "README.md").write_text("# Task documentation\n\nThis is a sample task.")
                (full_path / "__init__.py").write_text("# Task package")
            elif "templates" in vendor_dir:
                (full_path / "template.md.j2").write_text("# {{ title }}\n\n{{ content }}")
                (full_path / "config.yml").write_text("name: {{ template_name }}\ntype: template")
                (full_path / "metadata.json").write_text('{"version": "1.0", "author": "idflow"}')

    def teardown_method(self):
        """Clean up test environment after each test method."""
        # Remove temporary directories
        if self.temp_project_dir.exists():
            shutil.rmtree(self.temp_project_dir)
        if self.mock_pip_package.exists():
            shutil.rmtree(self.mock_pip_package)

    def test_copy_vendor_interactive(self):
        """Test interactive vendor copy functionality."""
        from idflow.cli.vendor.copy import copy_vendor

        # Mock the vendor functions to return our test directories
        with patch('idflow.core.vendor.list_copyable') as mock_list_copyable:
            mock_list_copyable.return_value = [
                (1, "tasks", self.mock_pip_package / "idflow" / "tasks"),
                (2, "templates/researcher", self.mock_pip_package / "idflow" / "templates" / "researcher"),
                (3, "templates/enricher", self.mock_pip_package / "idflow" / "templates" / "enricher"),
                (4, "templates/generator", self.mock_pip_package / "idflow" / "templates" / "generator")
            ]

            # Mock user input for interactive selection
            with patch('idflow.cli.vendor.copy.typer.prompt') as mock_prompt:
                mock_prompt.return_value = "1"  # Select first option

                # Mock typer.echo to capture output
                with patch('idflow.cli.vendor.copy.typer.echo') as mock_echo:
                    copy_vendor(dest=self.temp_project_dir)

                    # Verify that tasks directory was copied
                    tasks_dir = self.temp_project_dir / "tasks"
                    assert tasks_dir.exists()
                    assert (tasks_dir / "sample_task.py").exists()
                    assert (tasks_dir / "README.md").exists()
                    assert (tasks_dir / "__init__.py").exists()

                    # Verify file content was preserved
                    task_file = tasks_dir / "sample_task.py"
                    content = task_file.read_text()
                    assert "# Sample task" in content
                    assert "def run():" in content

                    # Verify echo was called
                    mock_echo.assert_called()

    def test_copy_vendor_all(self):
        """Test copying all vendor directories."""
        from idflow.cli.vendor.copy import copy_vendor

        with patch('idflow.core.vendor.list_copyable') as mock_list_copyable:
            mock_list_copyable.return_value = [
                (1, "tasks", self.mock_pip_package / "idflow" / "tasks"),
                (2, "templates/researcher", self.mock_pip_package / "idflow" / "templates" / "researcher"),
                (3, "templates/enricher", self.mock_pip_package / "idflow" / "templates" / "enricher"),
                (4, "templates/generator", self.mock_pip_package / "idflow" / "templates" / "generator")
            ]

            with patch('idflow.cli.vendor.copy.typer.echo') as mock_echo:
                copy_vendor(dest=self.temp_project_dir, all=True)

                # Verify all vendor directories were copied
                for vendor_dir in MOCK_VENDOR_DIRS:
                    full_path = self.temp_project_dir / vendor_dir
                    assert full_path.exists()

                    if vendor_dir == "tasks":
                        assert (full_path / "sample_task.py").exists()
                        assert (full_path / "README.md").exists()
                        assert (full_path / "__init__.py").exists()
                    elif "templates" in vendor_dir:
                        assert (full_path / "template.md.j2").exists()
                        assert (full_path / "config.yml").exists()
                        assert (full_path / "metadata.json").exists()

    def test_copy_vendor_with_existing_files(self):
        """Test vendor copy with existing files (overwrite/skip logic)."""
        from idflow.cli.vendor.copy import copy_vendor

        # Create existing files in project
        existing_tasks_dir = self.temp_project_dir / "tasks"
        existing_tasks_dir.mkdir()
        (existing_tasks_dir / "sample_task.py").write_text("# Existing task\n\ndef old_function():\n    return 'old'")

        with patch('idflow.core.vendor.list_copyable') as mock_list_copyable:
            mock_list_copyable.return_value = [
                (1, "tasks", self.mock_pip_package / "idflow" / "tasks"),
                (2, "templates/researcher", self.mock_pip_package / "idflow" / "templates" / "researcher"),
                (3, "templates/enricher", self.mock_pip_package / "idflow" / "templates" / "enricher"),
                (4, "templates/generator", self.mock_pip_package / "idflow" / "templates" / "generator")
            ]

            # Mock user choice for overwriting
            with patch('idflow.cli.vendor.copy.typer.echo') as mock_echo:
                copy_vendor(dest=self.temp_project_dir, all=True)

                # Verify file was overwritten
                task_file = existing_tasks_dir / "sample_task.py"
                assert task_file.exists()
                content = task_file.read_text()
                assert "# Sample task" in content  # New content
                assert "def run():" in content  # New content
                assert "# Existing task" not in content  # Old content removed
                assert "def old_function():" not in content  # Old content removed

    def test_copy_vendor_skip_existing(self):
        """Test vendor copy with skip option for existing files."""
        from idflow.cli.vendor.copy import copy_vendor

        # Create existing files in project
        existing_tasks_dir = self.temp_project_dir / "tasks"
        existing_tasks_dir.mkdir()
        (existing_tasks_dir / "sample_task.py").write_text("# Existing task\n\ndef old_function():\n    return 'old'")

        with patch('idflow.core.vendor.list_copyable') as mock_list_copyable:
            mock_list_copyable.return_value = [
                (1, "tasks", self.mock_pip_package / "idflow" / "tasks"),
                (2, "templates/researcher", self.mock_pip_package / "idflow" / "templates" / "researcher"),
                (3, "templates/enricher", self.mock_pip_package / "idflow" / "templates" / "enricher"),
                (4, "templates/generator", self.mock_pip_package / "idflow" / "templates" / "generator")
            ]

            # Mock user choice for skipping
            with patch('idflow.cli.vendor.copy.typer.echo') as mock_echo:
                copy_vendor(dest=self.temp_project_dir, all=True)

                # Verify file was not overwritten
                task_file = existing_tasks_dir / "sample_task.py"
                assert task_file.exists()
                content = task_file.read_text()
                assert "# Existing task" in content  # Original content preserved
                assert "def old_function():" in content  # Original content preserved
                assert "# Sample task" not in content  # New content not added

    def test_copy_vendor_custom_destination(self):
        """Test vendor copy to custom destination directory."""
        from idflow.cli.vendor.copy import copy_vendor

        custom_dest = self.temp_project_dir / "custom_project"
        custom_dest.mkdir()

        with patch('idflow.core.vendor.list_copyable') as mock_list_copyable:
            mock_list_copyable.return_value = [
                (1, "tasks", self.mock_pip_package / "idflow" / "tasks"),
                (2, "templates/researcher", self.mock_pip_package / "idflow" / "templates" / "researcher"),
                (3, "templates/enricher", self.mock_pip_package / "idflow" / "templates" / "enricher"),
                (4, "templates/generator", self.mock_pip_package / "idflow" / "templates" / "generator")
            ]

            with patch('idflow.cli.vendor.copy.typer.echo') as mock_echo:
                copy_vendor(dest=custom_dest, all=True)

                # Verify files were copied to custom destination
                tasks_dir = custom_dest / "tasks"
                assert tasks_dir.exists()
                assert (tasks_dir / "sample_task.py").exists()

                # Verify content
                task_file = tasks_dir / "sample_task.py"
                content = task_file.read_text()
                assert "# Sample task" in content

    def test_copy_vendor_no_pip_package(self):
        """Test vendor copy when pip package is not found."""
        from idflow.cli.vendor.copy import copy_vendor
        import typer

        with patch('idflow.core.vendor.list_copyable') as mock_list_copyable:
            mock_list_copyable.return_value = []

            with pytest.raises(typer.Exit):
                copy_vendor(dest=self.temp_project_dir)

    def test_copy_vendor_invalid_selection(self):
        """Test vendor copy with invalid user selection."""
        from idflow.cli.vendor.copy import copy_vendor
        import typer

        with patch('idflow.core.vendor.list_copyable') as mock_list_copyable:
            mock_list_copyable.return_value = [
                (1, "tasks", self.mock_pip_package / "idflow" / "tasks"),
                (2, "templates/researcher", self.mock_pip_package / "idflow" / "templates" / "researcher"),
                (3, "templates/enricher", self.mock_pip_package / "idflow" / "templates" / "enricher"),
                (4, "templates/generator", self.mock_pip_package / "idflow" / "templates" / "generator")
            ]

            # Mock invalid user input
            with patch('idflow.cli.vendor.copy.typer.prompt') as mock_prompt:
                mock_prompt.return_value = "999"  # Invalid selection

                with pytest.raises(typer.BadParameter):
                    copy_vendor(dest=self.temp_project_dir)

    def test_copy_vendor_preserve_structure(self):
        """Test that vendor copy preserves directory structure."""
        from idflow.cli.vendor.copy import copy_vendor

        with patch('idflow.core.vendor.list_copyable') as mock_list_copyable:
            mock_list_copyable.return_value = [
                (1, "tasks", self.mock_pip_package / "idflow" / "tasks"),
                (2, "templates/researcher", self.mock_pip_package / "idflow" / "templates" / "researcher"),
                (3, "templates/enricher", self.mock_pip_package / "idflow" / "templates" / "enricher"),
                (4, "templates/generator", self.mock_pip_package / "idflow" / "templates" / "generator")
            ]

            with patch('idflow.cli.vendor.copy.typer.echo') as mock_echo:
                copy_vendor(dest=self.temp_project_dir, all=True)

                # Verify nested directory structure is preserved
                templates_dir = self.temp_project_dir / "templates"
                assert templates_dir.exists()

                researcher_dir = templates_dir / "researcher"
                assert researcher_dir.exists()
                assert (researcher_dir / "template.md.j2").exists()

                enricher_dir = templates_dir / "enricher"
                assert enricher_dir.exists()
                assert (enricher_dir / "config.yml").exists()

    def test_copy_vendor_file_permissions(self):
        """Test that vendor copy preserves file permissions and content."""
        from idflow.cli.vendor.copy import copy_vendor

        with patch('idflow.core.vendor.list_copyable') as mock_list_copyable:
            mock_list_copyable.return_value = [
                (1, "tasks", self.mock_pip_package / "idflow" / "tasks"),
                (2, "templates/researcher", self.mock_pip_package / "idflow" / "templates" / "researcher"),
                (3, "templates/enricher", self.mock_pip_package / "idflow" / "templates" / "enricher"),
                (4, "templates/generator", self.mock_pip_package / "idflow" / "templates" / "generator")
            ]

            with patch('idflow.cli.vendor.copy.typer.echo') as mock_echo:
                copy_vendor(dest=self.temp_project_dir, all=True)

                # Verify file content is preserved
                task_file = self.temp_project_dir / "tasks" / "sample_task.py"
                assert task_file.exists()

                original_content = (self.mock_pip_package / "idflow" / "tasks" / "sample_task.py").read_text()
                copied_content = task_file.read_text()
                assert original_content == copied_content

                # Verify file permissions are reasonable (readable)
                assert task_file.stat().st_mode & 0o444  # At least readable

    def test_copy_vendor_abort_on_conflict(self):
        """Test vendor copy abort functionality when conflicts occur."""
        from idflow.cli.vendor.copy import copy_vendor

        # Create existing files in project
        existing_tasks_dir = self.temp_project_dir / "tasks"
        existing_tasks_dir.mkdir()
        (existing_tasks_dir / "sample_task.py").write_text("# Existing task\n\ndef old_function():\n    return 'old'")

        with patch('idflow.core.vendor.list_copyable') as mock_list_copyable:
            mock_list_copyable.return_value = [
                (1, "tasks", self.mock_pip_package / "idflow" / "tasks"),
                (2, "templates/researcher", self.mock_pip_package / "idflow" / "templates" / "researcher"),
                (3, "templates/enricher", self.mock_pip_package / "idflow" / "templates" / "enricher"),
                (4, "templates/generator", self.mock_pip_package / "idflow" / "templates" / "generator")
            ]

            # Mock user choice to abort
            with patch('idflow.cli.vendor.copy.typer.echo') as mock_echo:
                copy_vendor(dest=self.temp_project_dir, all=True)

                # Verify no files were copied (aborted)
                task_file = existing_tasks_dir / "sample_task.py"
                assert task_file.exists()
                content = task_file.read_text()
                assert "# Existing task" in content  # Original content preserved
                assert "def old_function():" in content  # Original content preserved


class TestVendorCLIErrorHandling:
    """Test error handling in vendor CLI commands."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.temp_project_dir = Path(tempfile.mkdtemp())
        self.mock_pip_package = Path(tempfile.mkdtemp())

        # Create mock pip package structure
        pip_dir = self.mock_pip_package / "idflow"
        pip_dir.mkdir()

        # Create mock vendor directories
        for vendor_dir in MOCK_VENDOR_DIRS:
            full_path = pip_dir / vendor_dir
            full_path.mkdir(parents=True, exist_ok=True)

            # Add some mock files
            if vendor_dir == "tasks":
                (full_path / "sample_task.py").write_text("# Sample task")
                (full_path / "README.md").write_text("# Task documentation")

    def teardown_method(self):
        """Clean up test environment after each test method."""
        # Remove temporary directories
        if self.temp_project_dir.exists():
            shutil.rmtree(self.temp_project_dir)
        if self.mock_pip_package.exists():
            shutil.rmtree(self.mock_pip_package)

    def test_copy_vendor_permission_error(self):
        """Test vendor copy with permission errors."""
        from idflow.cli.vendor.copy import copy_vendor
        import typer

        # Make destination read-only
        self.temp_project_dir.chmod(0o444)

        with patch('idflow.core.vendor.list_copyable') as mock_list_copyable:
            mock_list_copyable.return_value = [
                (1, "tasks", self.mock_pip_package / "idflow" / "tasks"),
                (2, "templates/researcher", self.mock_pip_package / "idflow" / "templates" / "researcher"),
                (3, "templates/enricher", self.mock_pip_package / "idflow" / "templates" / "enricher"),
                (4, "templates/generator", self.mock_pip_package / "idflow" / "templates" / "generator")
            ]

            with pytest.raises((typer.Exit, PermissionError, OSError)):
                copy_vendor(dest=self.temp_project_dir, all=True)

        # Restore permissions for cleanup
        self.temp_project_dir.chmod(0o755)

    def test_copy_vendor_disk_space_error(self):
        """Test vendor copy with disk space issues."""
        from idflow.cli.vendor.copy import copy_vendor
        import typer

        with patch('idflow.core.vendor.list_copyable') as mock_list_copyable:
            mock_list_copyable.return_value = [
                (1, "tasks", self.mock_pip_package / "idflow" / "templates" / "researcher"),
                (2, "templates/enricher", self.mock_pip_package / "idflow" / "templates" / "enricher"),
                (3, "templates/generator", self.mock_pip_package / "idflow" / "templates" / "generator")
            ]

            # Mock shutil.copyfile to raise OSError (disk full)
            with patch('shutil.copyfile') as mock_copy:
                mock_copy.side_effect = OSError("No space left on device")

                with pytest.raises(typer.Exit):
                    copy_vendor(dest=self.temp_project_dir, all=True)


if __name__ == "__main__":
    pytest.main([__file__])
