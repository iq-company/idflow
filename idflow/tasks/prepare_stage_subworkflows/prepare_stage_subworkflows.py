# TYPE: PREPARE_STAGE_SUBWORKFLOWS

from conductor.client.worker.worker_task import worker_task
from typing import Dict, Any, List
from idflow.core.stage_definitions import get_stage_definitions
from idflow.core.workflow_manager import get_workflow_manager


@worker_task(task_definition_name='prepare_stage_subworkflows')
def prepare_stage_subworkflows(
    docId: str,
    stageName: str,
    stageCounter: int
) -> Dict[str, Any]:
    """
    Prepare dynamic fork tasks for a stage based on its definition.

    Args:
        docId: Document ID
        stageName: Name of the stage
        stageCounter: Stage counter

    Returns:
        Dictionary with dynamicForkTasksParam and dynamicForkTasksInputParamName
    """
    try:
        # Get stage definition
        stage_definitions = get_stage_definitions()
        stage_definition = stage_definitions.get_definition(stageName)

        if not stage_definition:
            print(f"Warning: Stage definition '{stageName}' not found. Available stages: {stage_definitions.list_definitions()}")
            # Return empty task lists if stage definition not found
            return {
                "subWorkflowTasksParam": [],
                "subWorkflowTasksInput": {},
                "persistTasksParam": [],
                "persistTasksInput": {}
            }

        # Get workflow manager for version information
        workflow_manager = get_workflow_manager()

        # Prepare dynamic fork tasks - each fork contains sub-workflow + persist task in sequence
        dynamic_fork_tasks = []

        # Generate input map for wrapper tasks
        dynamic_tasks_input = {}

        for i, wf in enumerate(stage_definition.workflows, 1):
            # Get the local workflow version
            local_workflow_file = workflow_manager.find_workflow_file(wf.name)
            local_version = 1
            if local_workflow_file and (local_workflow_def := workflow_manager.load_workflow_definition(local_workflow_file)):
                local_version = local_workflow_def.get('version', 1)

            # Create a SUB_WORKFLOW task that wraps the sub-workflow + persist logic
            wrapper_task = {
                "name": f"wrap_{wf.name}_{i}",
                "taskReferenceName": f"wrap_{wf.name}_{i}",
                "type": "SUB_WORKFLOW",
                "subWorkflowParam": {
                    "name": "wrap_stage_subworkflow"
                },
                "inputParameters": {
                    "docId": "${workflow.input.docId}",
                    "stageName": "${workflow.input.stageName}",
                    "stageCounter": "${workflow.input.stageCounter}",
                    "subworkflow_name": wf.name,
                    "subworkflow_version": local_version
                }
            }

            # Add workflow-specific inputs if provided
            if wf.inputs:
                wrapper_task["inputParameters"].update(wf.inputs)

            dynamic_fork_tasks.append(wrapper_task)

            # Input for the wrapper task
            wrapper_ref_name = f"wrap_{wf.name}_{i}"
            wrapper_inputs = {
                "docId": "${workflow.input.docId}",
                "stageName": "${workflow.input.stageName}",
                "stageCounter": "${workflow.input.stageCounter}",
                "subworkflow_name": wf.name
            }

            # Add workflow-specific inputs if provided
            if wf.inputs:
                wrapper_inputs.update(wf.inputs)

            dynamic_tasks_input[wrapper_ref_name] = wrapper_inputs

        # Return the configuration for single FORK_JOIN_DYNAMIC
        return {
            "dynamicForkTasksParam": dynamic_fork_tasks,
            "dynamicForkTasksInput": dynamic_tasks_input,
            "dynamicForkTasksInputParamName": "dynamicTasksInput"
        }

    except Exception as e:
        print(f"Error in prepare_stage_subworkflows: {e}")
        import traceback
        traceback.print_exc()
        # Return empty task lists on error
        return {
            "subWorkflowTasksParam": [],
            "subWorkflowTasksInput": {},
            "persistTasksParam": [],
            "persistTasksInput": {}
        }
