"""
Tests for the prepare_stage_subworkflows task.
"""

import pytest
from unittest.mock import patch, MagicMock
from idflow.tasks.prepare_stage_subworkflows.prepare_stage_subworkflows import prepare_stage_subworkflows


class TestPrepareStageSubworkflows:
    """Test cases for the prepare_stage_subworkflows task."""

    @patch('idflow.tasks.prepare_stage_subworkflows.prepare_stage_subworkflows.get_stage_definitions')
    @patch('idflow.tasks.prepare_stage_subworkflows.prepare_stage_subworkflows.get_workflow_manager')
    def test_prepare_single_workflow(self, mock_get_workflow_manager, mock_get_stage_definitions):
        """Test preparing a single workflow."""
        # Mock stage definition
        mock_workflow = MagicMock()
        mock_workflow.name = "research_blog_post_ideas"
        mock_workflow.inputs = {"research_methods": ["gpt_researcher", "duckduckgo_serp"]}
        mock_workflow.when = "doc.tags && doc.tags.includes('blog_post_ideas')"

        mock_stage_def = MagicMock()
        mock_stage_def.workflows = [mock_workflow]

        mock_stage_definitions = MagicMock()
        mock_stage_definitions.get_definition.return_value = mock_stage_def
        mock_get_stage_definitions.return_value = mock_stage_definitions

        # Mock workflow manager
        mock_workflow_manager = MagicMock()
        mock_workflow_manager.find_workflow_file.return_value = "workflow_file.json"
        mock_workflow_manager.load_workflow_definition.return_value = {"version": 2}
        mock_get_workflow_manager.return_value = mock_workflow_manager

        result = prepare_stage_subworkflows(
            docId="doc-123",
            stageName="research_blog_post_ideas",
            stageCounter=1
        )

        # Verify the result structure
        assert "dynamicForkTasksParam" in result
        assert "dynamicForkTasksInput" in result
        assert "dynamicForkTasksInputParamName" in result
        assert result["dynamicForkTasksInputParamName"] == "dynamicTasksInput"

        # Verify fork tasks (should be list of task objects)
        fork_tasks = result["dynamicForkTasksParam"]
        assert len(fork_tasks) == 1

        fork_task = fork_tasks[0]
        assert fork_task["name"] == "sub_workflow_1"
        assert fork_task["taskReferenceName"] == "sub1"
        assert fork_task["type"] == "SUB_WORKFLOW"
        assert fork_task["subWorkflowParam"]["name"] == "research_blog_post_ideas"
        assert fork_task["subWorkflowParam"]["version"] == 2

        # Verify input parameters in fork task definition
        input_params = fork_task["inputParameters"]
        assert input_params["docId"] == "${workflow.input.docId}"
        assert input_params["stageName"] == "${workflow.input.stageName}"
        assert input_params["stageCounter"] == "${workflow.input.stageCounter}"
        assert input_params["research_methods"] == ["gpt_researcher", "duckduckgo_serp"]

        # Verify dynamic tasks input map
        dynamic_input = result["dynamicForkTasksInput"]
        assert "sub1" in dynamic_input
        sub1_input = dynamic_input["sub1"]
        assert sub1_input["docId"] == "${workflow.input.docId}"
        assert sub1_input["stageName"] == "${workflow.input.stageName}"
        assert sub1_input["stageCounter"] == "${workflow.input.stageCounter}"
        assert sub1_input["research_methods"] == ["gpt_researcher", "duckduckgo_serp"]

    @patch('idflow.tasks.prepare_stage_subworkflows.prepare_stage_subworkflows.get_stage_definitions')
    @patch('idflow.tasks.prepare_stage_subworkflows.prepare_stage_subworkflows.get_workflow_manager')
    def test_prepare_multiple_workflows(self, mock_get_workflow_manager, mock_get_stage_definitions):
        """Test preparing multiple workflows."""
        # Mock stage definition with multiple workflows
        mock_workflow1 = MagicMock()
        mock_workflow1.name = "research_blog_post_ideas"
        mock_workflow1.inputs = {"research_methods": ["gpt_researcher"]}
        mock_workflow1.when = "doc.tags && doc.tags.includes('blog_post_ideas')"

        mock_workflow2 = MagicMock()
        mock_workflow2.name = "create_blog_post_draft"
        mock_workflow2.inputs = {"prompt_template": "create_blog_post_draft"}
        mock_workflow2.when = "true"

        mock_stage_def = MagicMock()
        mock_stage_def.workflows = [mock_workflow1, mock_workflow2]

        mock_stage_definitions = MagicMock()
        mock_stage_definitions.get_definition.return_value = mock_stage_def
        mock_get_stage_definitions.return_value = mock_stage_definitions

        # Mock workflow manager
        mock_workflow_manager = MagicMock()
        mock_workflow_manager.find_workflow_file.return_value = "workflow_file.json"
        mock_workflow_manager.load_workflow_definition.return_value = {"version": 1}
        mock_get_workflow_manager.return_value = mock_workflow_manager

        result = prepare_stage_subworkflows(
            docId="doc-123",
            stageName="multi_workflow_stage",
            stageCounter=1
        )

        # Verify fork tasks (should be list of task objects)
        fork_tasks = result["dynamicForkTasksParam"]
        assert len(fork_tasks) == 2

        # Verify first workflow
        fork_task_1 = fork_tasks[0]
        assert fork_task_1["name"] == "sub_workflow_1"
        assert fork_task_1["taskReferenceName"] == "sub1"
        assert fork_task_1["subWorkflowParam"]["name"] == "research_blog_post_ideas"
        assert fork_task_1["inputParameters"]["research_methods"] == ["gpt_researcher"]

        # Verify second workflow
        fork_task_2 = fork_tasks[1]
        assert fork_task_2["name"] == "sub_workflow_2"
        assert fork_task_2["taskReferenceName"] == "sub2"
        assert fork_task_2["subWorkflowParam"]["name"] == "create_blog_post_draft"
        assert fork_task_2["inputParameters"]["prompt_template"] == "create_blog_post_draft"

    @patch('idflow.tasks.prepare_stage_subworkflows.prepare_stage_subworkflows.get_stage_definitions')
    @patch('idflow.tasks.prepare_stage_subworkflows.prepare_stage_subworkflows.get_workflow_manager')
    def test_prepare_workflow_without_inputs(self, mock_get_workflow_manager, mock_get_stage_definitions):
        """Test preparing workflow without additional inputs."""
        # Mock stage definition
        mock_workflow = MagicMock()
        mock_workflow.name = "simple_workflow"
        mock_workflow.inputs = None
        mock_workflow.when = "true"

        mock_stage_def = MagicMock()
        mock_stage_def.workflows = [mock_workflow]

        mock_stage_definitions = MagicMock()
        mock_stage_definitions.get_definition.return_value = mock_stage_def
        mock_get_stage_definitions.return_value = mock_stage_definitions

        # Mock workflow manager
        mock_workflow_manager = MagicMock()
        mock_workflow_manager.find_workflow_file.return_value = "workflow_file.json"
        mock_workflow_manager.load_workflow_definition.return_value = {"version": 1}
        mock_get_workflow_manager.return_value = mock_workflow_manager

        result = prepare_stage_subworkflows(
            docId="doc-123",
            stageName="simple_stage",
            stageCounter=1
        )

        # Verify fork tasks (should be list of task objects)
        fork_tasks = result["dynamicForkTasksParam"]
        assert len(fork_tasks) == 1

        fork_task = fork_tasks[0]
        assert fork_task["subWorkflowParam"]["name"] == "simple_workflow"

        # Verify input parameters only contain standard ones
        input_params = fork_task["inputParameters"]
        assert "docId" in input_params
        assert "stageName" in input_params
        assert "stageCounter" in input_params
        # Should not have any workflow-specific inputs
        assert len(input_params) == 3

    @patch('idflow.tasks.prepare_stage_subworkflows.prepare_stage_subworkflows.get_stage_definitions')
    def test_stage_definition_not_found(self, mock_get_stage_definitions):
        """Test handling when stage definition is not found."""
        mock_stage_definitions = MagicMock()
        mock_stage_definitions.get_definition.return_value = None
        mock_get_stage_definitions.return_value = mock_stage_definitions

        with pytest.raises(ValueError, match="Stage definition 'nonexistent_stage' not found"):
            prepare_stage_subworkflows(
                docId="doc-123",
                stageName="nonexistent_stage",
                stageCounter=1
            )

    @patch('idflow.tasks.prepare_stage_subworkflows.prepare_stage_subworkflows.get_stage_definitions')
    @patch('idflow.tasks.prepare_stage_subworkflows.prepare_stage_subworkflows.get_workflow_manager')
    def test_workflow_version_fallback(self, mock_get_workflow_manager, mock_get_stage_definitions):
        """Test fallback to version 1 when workflow file not found."""
        # Mock stage definition
        mock_workflow = MagicMock()
        mock_workflow.name = "workflow_without_file"
        mock_workflow.inputs = {}
        mock_workflow.when = "true"

        mock_stage_def = MagicMock()
        mock_stage_def.workflows = [mock_workflow]

        mock_stage_definitions = MagicMock()
        mock_stage_definitions.get_definition.return_value = mock_stage_def
        mock_get_stage_definitions.return_value = mock_stage_definitions

        # Mock workflow manager - file not found
        mock_workflow_manager = MagicMock()
        mock_workflow_manager.find_workflow_file.return_value = None
        mock_get_workflow_manager.return_value = mock_workflow_manager

        result = prepare_stage_subworkflows(
            docId="doc-123",
            stageName="test_stage",
            stageCounter=1
        )

        # Verify fallback to version 1
        fork_tasks = result["dynamicForkTasksParam"]
        fork_task = fork_tasks[0]
        assert fork_task["subWorkflowParam"]["version"] == 1
