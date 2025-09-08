# TYPE: UPDATE_STAGE_STATUS

from conductor.client.worker.worker_task import worker_task
from idflow.core.document_factory import get_document_class


@worker_task(task_definition_name='update_stage_status')
def update_stage_status(docId: str, stageName: str, stageCounter: int, status: str) -> dict:
    """
    Update the status of a specific stage instance.

    Args:
        docId: Document ID
        stageName: Name of the stage
        stageCounter: Counter of the stage instance
        status: New status to set

    Returns:
        dict: Update result
    """
    try:
        # Find the document
        # Load the document using factory
        DocumentClass = get_document_class()
        doc = DocumentClass.find(docId)
        if not doc:
            return {
                "success": False,
                "error": f"Document {docId} not found",
                "docId": docId,
                "stageName": stageName,
                "stageCounter": stageCounter
            }

        # Find the stage
        stage = doc.get_stage(stageName, stageCounter)
        if not stage:
            return {
                "success": False,
                "error": f"Stage {stageName} (counter {stageCounter}) not found",
                "docId": docId,
                "stageName": stageName,
                "stageCounter": stageCounter
            }

        # Update stage status
        old_status = stage.status
        stage.status = status

        # Save the stage (this should be sufficient)
        doc.save()

        return {
            "success": True,
            "message": f"Stage {stageName} (counter {stageCounter}) status updated from {old_status} to {status}",
            "docId": docId,
            "stageName": stageName,
            "stageCounter": stageCounter,
            "oldStatus": old_status,
            "newStatus": status
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update stage status: {str(e)}",
            "docId": docId,
            "stageName": stageName,
            "stageCounter": stageCounter
        }

