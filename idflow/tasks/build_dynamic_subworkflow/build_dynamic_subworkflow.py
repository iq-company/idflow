from typing import Any, Dict
from conductor.client.worker.worker_task import worker_task


@worker_task(task_definition_name='build_dynamic_subworkflow')
def build_dynamic_subworkflow(
    subworkflow_name: str,
    subworkflow_version: int,
    docId: str,
    stageName: str,
    stageCounter: int,
    extraInputs: Any = None,
) -> dict:
    """
    Build a single SUB_WORKFLOW task definition (with fixed Integer version) for use in a FORK_JOIN_DYNAMIC.

    Returns a payload with keys:
      - dynamicTasks: list[WorkflowTask]
      - dynamicTasksInput: dict[str, dict]
    """
    sub_task_ref = 'inner_sub'

    task: dict = {
        "name": subworkflow_name,
        "taskReferenceName": sub_task_ref,
        "type": "SUB_WORKFLOW",
        "subWorkflowParam": {
            "name": subworkflow_name,
            "version": int(subworkflow_version),
        },
        "inputParameters": {
            "docId": docId,
            "stageName": stageName,
            "stageCounter": stageCounter,
        },
    }

    if extraInputs:
        task["inputParameters"].update(extraInputs)

    return {
        "dynamicTasks": [task],
        "dynamicTasksInput": {sub_task_ref: {}},
    }

