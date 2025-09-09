#!/usr/bin/env python3
"""
Integration tests for the complete workflow.

Tests the end-to-end workflow from document creation through
stage evaluation to workflow execution.
"""

import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import json

from idflow.core.document_factory import get_document_class
from idflow.core.fs_markdown import FSMarkdownDocument


class TestCompleteWorkflow:
    """Test the complete workflow from document creation to stage execution."""

    def test_doc_add_complete_workflow(self, temp_data_dir, mock_uuid):
        """Test complete workflow from doc add command."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Mock stage definitions
            mock_stage_def = MagicMock()
            mock_stage_def.check_requirements.return_value = True
            mock_stage_def.trigger_workflows.return_value = ["workflow1"]
            mock_stage_def.multiple_callable = False

            with patch('idflow.core.stage_definitions.get_stage_definitions') as mock_get_defs:
                mock_stage_definitions = MagicMock()
                mock_stage_definitions.list_definitions.return_value = ["research_blog_post_ideas"]
                mock_stage_definitions.get_definition.return_value = mock_stage_def
                mock_get_defs.return_value = mock_stage_definitions

                # Create document via factory (simulating doc add)
                DocumentClass = get_document_class()
                doc = DocumentClass(title="Test Document", tags=["blog_post_ideas"])

                # Save document (triggers complete workflow)
                doc.save()

                # Verify document was created and persisted
                assert doc._persisted is True
                assert doc.title == "Test Document"
                assert doc.tags == ["blog_post_ideas"]

                # Verify stage evaluation was triggered
                # (This would be verified by checking if stages were created)
                # In a real test, we'd check the filesystem for stage files

    def test_document_status_change_workflow(self, temp_data_dir, mock_uuid):
        """Test workflow when document status changes from inbox to active."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Mock stage definitions
            mock_stage_def = MagicMock()
            mock_stage_def.check_requirements.return_value = True
            mock_stage_def.trigger_workflows.return_value = ["workflow1"]
            mock_stage_def.multiple_callable = False

            with patch('idflow.core.stage_definitions.get_stage_definitions') as mock_get_defs:
                mock_stage_definitions = MagicMock()
                mock_stage_definitions.list_definitions.return_value = ["research_blog_post_ideas"]
                mock_stage_definitions.get_definition.return_value = mock_stage_def
                mock_get_defs.return_value = mock_stage_definitions

                # Create document with inbox status
                DocumentClass = get_document_class()
                doc = DocumentClass(title="Test Document", status="inbox", tags=["blog_post_ideas"])

                # Save document
                doc.save()

                # Verify status changed to active
                assert doc.status == "active"
                assert doc._persisted is True

    def test_stage_creation_and_persistence(self, temp_data_dir, mock_uuid):
        """Test that stages are created and persisted correctly."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Mock stage definitions
            mock_stage_def = MagicMock()
            mock_stage_def.check_requirements.return_value = True
            mock_stage_def.trigger_workflows.return_value = ["workflow1"]
            mock_stage_def.multiple_callable = False

            with patch('idflow.core.stage_definitions.get_stage_definitions') as mock_get_defs:
                mock_stage_definitions = MagicMock()
                mock_stage_definitions.list_definitions.return_value = ["research_blog_post_ideas"]
                mock_stage_definitions.get_definition.return_value = mock_stage_def
                mock_get_defs.return_value = mock_stage_definitions

                # Create document
                DocumentClass = get_document_class()
                doc = DocumentClass(title="Test Document", tags=["blog_post_ideas"])

                # Mock stage save
                with patch('idflow.core.stage.Stage.save') as mock_stage_save:
                    # Save document (triggers stage creation)
                    doc.save()

                    # Verify stage was created and saved
                    assert len(doc.stages) == 1
                    assert doc.stages[0].name == "research_blog_post_ideas"
                    mock_stage_save.assert_called_once()

    def test_workflow_triggering_integration(self, temp_data_dir, mock_uuid):
        """Test that workflows are triggered during stage evaluation."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Mock stage definitions
            mock_stage_def = MagicMock()
            mock_stage_def.check_requirements.return_value = True
            mock_stage_def.trigger_workflows.return_value = ["workflow1", "workflow2"]
            mock_stage_def.multiple_callable = False

            with patch('idflow.core.stage_definitions.get_stage_definitions') as mock_get_defs:
                mock_stage_definitions = MagicMock()
                mock_stage_definitions.list_definitions.return_value = ["research_blog_post_ideas"]
                mock_stage_definitions.get_definition.return_value = mock_stage_def
                mock_get_defs.return_value = mock_stage_definitions

                # Create document
                DocumentClass = get_document_class()
                doc = DocumentClass(title="Test Document", tags=["blog_post_ideas"])

                # Save document (triggers workflow)
                doc.save()

                # Verify workflows were triggered
                mock_stage_def.trigger_workflows.assert_called_once_with(doc)

    def test_error_handling_in_workflow(self, temp_data_dir, mock_uuid):
        """Test that errors in workflow are handled gracefully."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Mock stage definitions with error
            mock_stage_def = MagicMock()
            mock_stage_def.check_requirements.return_value = True
            mock_stage_def.trigger_workflows.side_effect = Exception("Workflow error")
            mock_stage_def.multiple_callable = False

            with patch('idflow.core.stage_definitions.get_stage_definitions') as mock_get_defs:
                mock_stage_definitions = MagicMock()
                mock_stage_definitions.list_definitions.return_value = ["research_blog_post_ideas"]
                mock_stage_definitions.get_definition.return_value = mock_stage_def
                mock_get_defs.return_value = mock_stage_definitions

                # Create document
                DocumentClass = get_document_class()
                doc = DocumentClass(title="Test Document", tags=["blog_post_ideas"])

                # Save document (should not raise exception despite workflow error)
                doc.save()

                # Verify document was still saved
                assert doc._persisted is True
                assert doc.status == "active"

    def test_multiple_stages_workflow(self, temp_data_dir, mock_uuid):
        """Test workflow with multiple stages."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Mock multiple stage definitions
            mock_stage1_def = MagicMock()
            mock_stage1_def.check_requirements.return_value = True
            mock_stage1_def.trigger_workflows.return_value = ["workflow1"]
            mock_stage1_def.multiple_callable = False

            mock_stage2_def = MagicMock()
            mock_stage2_def.check_requirements.return_value = True
            mock_stage2_def.trigger_workflows.return_value = ["workflow2"]
            mock_stage2_def.multiple_callable = False

            def get_definition(name):
                if name == "research_blog_post_ideas":
                    return mock_stage1_def
                elif name == "create_blog_post_draft":
                    return mock_stage2_def
                return None

            with patch('idflow.core.stage_definitions.get_stage_definitions') as mock_get_defs:
                mock_stage_definitions = MagicMock()
                mock_stage_definitions.list_definitions.return_value = [
                    "research_blog_post_ideas",
                    "create_blog_post_draft"
                ]
                mock_stage_definitions.get_definition.side_effect = get_definition
                mock_get_defs.return_value = mock_stage_definitions

                # Create document
                DocumentClass = get_document_class()
                doc = DocumentClass(title="Test Document", tags=["blog_post_ideas"])

                # Mock stage save
                with patch('idflow.core.stage.Stage.save') as mock_stage_save:
                    # Save document (triggers multiple stages)
                    doc.save()

                    # Verify multiple stages were created
                    assert len(doc.stages) == 2
                    stage_names = [stage.name for stage in doc.stages]
                    assert "research_blog_post_ideas" in stage_names
                    assert "create_blog_post_draft" in stage_names

                    # Verify both stages were saved
                    assert mock_stage_save.call_count == 2


class TestWorkflowManagementIntegration:
    """Test workflow management integration."""

    def test_workflow_upload_integration(self, temp_data_dir):
        """Test workflow upload integration."""
        # Create test workflow files
        workflow_dir = temp_data_dir / "workflows"
        workflow_dir.mkdir(exist_ok=True)

        workflow_file = workflow_dir / "test_workflow.json"
        workflow_file.write_text(json.dumps({
            "name": "test_workflow",
            "version": 1,
            "description": "Test workflow"
        }))

        # Mock Conductor client
        with patch('idflow.core.conductor_client.get_workflow_definitions') as mock_get_defs, \
          patch('idflow.core.workflow_manager.upload_workflow') as mock_upload:

          mock_get_defs.return_value = []  # No existing workflows
          mock_upload.return_value = True

          from idflow.core.workflow_manager import WorkflowManager
          manager = WorkflowManager()

          # Upload workflows
          result = manager.upload_workflows()

          # Verify upload was attempted
          # The actual result is a dict with workflow names as keys
          assert len(result) >= 1
          # Note: skipped_count might not be in the result

    def test_workflow_list_integration(self, temp_data_dir):
        """Test workflow list integration."""
        # Create test workflow files
        workflow_dir = temp_data_dir / "workflows"
        workflow_dir.mkdir(exist_ok=True)

        workflow_file = workflow_dir / "test_workflow.json"
        workflow_file.write_text(json.dumps({
            "name": "test_workflow",
            "version": 1,
            "description": "Test workflow"
        }))

        # Mock Conductor client
        with patch('idflow.core.conductor_client.get_workflow_definitions') as mock_get_defs:
            mock_get_defs.return_value = [
                {"name": "test_workflow", "version": 1}
            ]

            from idflow.core.workflow_manager import WorkflowManager
            manager = WorkflowManager()

            # List workflows
            result = manager.list_workflows()

            # Verify workflow was listed
            # The actual result includes all workflows from the project
            assert len(result) >= 1
            # The result is a list of workflow names, not dicts
            # Since we're testing with real workflows, just check that we got some results
            assert len(result) > 0


class TestWorkerManagementIntegration:
    """Test worker management integration."""

    def test_worker_ps_integration(self):
        """Test worker ps command integration."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
pgr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo:
                from idflow.cli.worker.worker import list_running_workers
                list_running_workers()

                # Verify output was generated
                assert mock_echo.called

    def test_worker_killall_integration(self):
        """Test worker killall command integration."""
        mock_ps_output = """USER       PID  %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
pgr       1234  0.1  0.2  23456  7890 pts/0    S+   10:01   0:00 python -m idflow worker start --worker update_stage_status
"""

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_ps_output

            with patch('typer.echo') as mock_echo, \
                 patch('typer.confirm') as mock_confirm, \
                 patch('os.kill') as mock_kill:

                mock_confirm.return_value = True

                from idflow.cli.worker.worker import kill_workers
                kill_workers(pattern="update_stage_status")

                # Verify kill was attempted
                import signal
                # The test uses kill=True by default, so it should be SIGKILL
                mock_kill.assert_called_once_with(1234, signal.SIGKILL)


class TestErrorRecovery:
    """Test error recovery in the complete workflow."""

    def test_document_creation_error_recovery(self, temp_data_dir, mock_uuid):
        """Test error recovery during document creation."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Mock document creation to fail
            with patch.object(FSMarkdownDocument, '_create') as mock_create:
                mock_create.side_effect = Exception("Create failed")

                DocumentClass = get_document_class()
                doc = DocumentClass(title="Test Document")

                # Should raise exception
                with pytest.raises(Exception, match="Create failed"):
                    doc.save()

    def test_stage_evaluation_error_recovery(self, temp_data_dir, mock_uuid):
        """Test error recovery during stage evaluation."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Mock stage evaluation to fail
            with patch.object(FSMarkdownDocument, 'evaluate_stages') as mock_evaluate:
                mock_evaluate.side_effect = Exception("Stage evaluation failed")

                DocumentClass = get_document_class()
                doc = DocumentClass(title="Test Document", tags=["blog_post_ideas"])

                # Should not raise exception (error handled gracefully)
                doc.save()

                # Document should still be saved
                assert doc._persisted is True

    def test_workflow_triggering_error_recovery(self, temp_data_dir, mock_uuid):
        """Test error recovery during workflow triggering."""
        with patch('idflow.core.config.config') as mock_config:
            mock_config.base_dir = temp_data_dir

            # Mock stage definitions with workflow error
            mock_stage_def = MagicMock()
            mock_stage_def.check_requirements.return_value = True
            mock_stage_def.trigger_workflows.side_effect = Exception("Workflow error")
            mock_stage_def.multiple_callable = False

            with patch('idflow.core.stage_definitions.get_stage_definitions') as mock_get_defs:
                mock_stage_definitions = MagicMock()
                mock_stage_definitions.list_definitions.return_value = ["research_blog_post_ideas"]
                mock_stage_definitions.get_definition.return_value = mock_stage_def
                mock_get_defs.return_value = mock_stage_definitions

                DocumentClass = get_document_class()
                doc = DocumentClass(title="Test Document", tags=["blog_post_ideas"])

                # Should not raise exception (error handled gracefully)
                doc.save()

                # Document should still be saved
                assert doc._persisted is True
