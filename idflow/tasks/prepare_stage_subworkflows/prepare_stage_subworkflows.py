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

    # Get stage definition
    stage_definitions = get_stage_definitions()
    stage_definition = stage_definitions.get_definition(stageName)

    if not stage_definition:
        raise ValueError(f"Stage definition '{stageName}' not found")

    # Get workflow manager for version information
    workflow_manager = get_workflow_manager()

    # Prepare dynamic fork tasks
    dynamic_fork_tasks = []

    for i, wf in enumerate(stage_definition.workflows, 1):
        # Get the local workflow version
        local_workflow_file = workflow_manager.find_workflow_file(wf.name)
        local_version = 1
        if local_workflow_file and (local_workflow_def := workflow_manager.load_workflow_definition(local_workflow_file)):
            local_version = local_workflow_def.get('version', 1)

        # Create fork task configuration
        fork_task = {
            "name": f"stage_wf_{wf.name}_{i}",
            "taskReferenceName": f"stage_wf_{wf.name}_{i}",
            "type": "SUB_WORKFLOW",
            "subWorkflowParam": {
                "name": wf.name,
                "version": local_version
            },
            "inputParameters": {
                "docId": "${workflow.input.docId}",
                "stageName": "${workflow.input.stageName}",
                "stageCounter": "${workflow.input.stageCounter}"
            }
        }

        # Add workflow-specific inputs if provided
        if wf.inputs:
            fork_task["inputParameters"].update(wf.inputs)

        dynamic_fork_tasks.append(fork_task)

    # Generate input map for each task
    dynamic_tasks_input = {}
    for i, wf in enumerate(stage_definition.workflows, 1):
        task_ref_name = f"sub{i}"
        task_inputs = {
            "docId": "${workflow.input.docId}",
            "stageName": "${workflow.input.stageName}",
            "stageCounter": "${workflow.input.stageCounter}"
        }

        # Add workflow-specific inputs if provided
        if wf.inputs:
            task_inputs.update(wf.inputs)

        dynamic_tasks_input[task_ref_name] = task_inputs

    # Return the configuration for FORK_JOIN_DYNAMIC
    # Conductor expects dynamicForkTasksParam as a list of task objects
    # and dynamicForkTasksInput as a map of taskReferenceName -> inputs
    return {
        "dynamicForkTasksParam": dynamic_fork_tasks,
        "dynamicForkTasksInput": dynamic_tasks_input,
        "dynamicForkTasksInputParamName": "dynamicTasksInput"
    }
