# TYPE: STAGE_EVALUATION

from conductor.client.worker.worker_task import worker_task
from idflow.core.document_factory import get_document_class
from idflow.core.stage_definitions import get_stage_definitions


@worker_task(task_definition_name='stage_evaluation')
def stage_evaluation(docId: str, triggered_by: str = None) -> dict:
    """
    Evaluate stages for a document and start new stages where requirements are met.

    Args:
        docId: Document ID to evaluate
        triggered_by: Workflow ID that triggered this evaluation

    Returns:
        dict: Evaluation results with started stages
    """
    try:
        # Get document class from factory
        DocumentClass = get_document_class()

        # Find the document
        doc = DocumentClass.find(docId)
        if not doc:
            return {
                "success": False,
                "error": f"Document {docId} not found",
                "docId": docId,
                "triggered_by": triggered_by
            }

        # Use document's evaluate_stages method
        result = doc.evaluate_stages()

        if not result["success"]:
            return {
                "success": False,
                "error": result.get("error", "Stage evaluation failed"),
                "docId": docId,
                "triggered_by": triggered_by
            }

        # Save document after evaluation
        doc.save()

        return {
            "success": True,
            "message": f"Stage evaluation completed for document {docId}",
            "docId": docId,
            "triggered_by": triggered_by,
            "stages_evaluated": result["stages_evaluated"],
            "stages_started": result["stages_started"],
            "stages_skipped": result["stages_skipped"],
            "started_stages": result["started_stages"],
            "skipped_stages": result["skipped_stages"],
            "status_changed": result["status_changed"],
            "document_status": result["document_status"]
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Stage evaluation failed: {str(e)}",
            "docId": docId,
            "triggered_by": triggered_by
        }

