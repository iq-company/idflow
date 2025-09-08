# TYPE: STAGE_EVALUATION

from conductor.client.worker.worker_task import worker_task
from idflow.core.fs_markdown import FSMarkdownDocument
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
        # Find the document
        doc = FSMarkdownDocument.find(docId)
        if not doc:
            return {
                "success": False,
                "error": f"Document {docId} not found",
                "docId": docId,
                "triggered_by": triggered_by
            }

        # Get stage definitions
        stage_definitions = get_stage_definitions()
        available_stages = stage_definitions.list_definitions()

        if not available_stages:
            return {
                "success": True,
                "message": "No stage definitions found",
                "docId": docId,
                "triggered_by": triggered_by,
                "stages_evaluated": 0,
                "stages_started": 0
            }

        # Track results
        stages_evaluated = 0
        stages_started = 0
        started_stages = []

        # Evaluate each stage
        for stage_name in available_stages:
            stage_def = stage_definitions.get_definition(stage_name)
            if not stage_def:
                continue

            # Check if stage already exists for this document
            existing_stages = doc.get_stages(stage_name)

            # Determine if we can create this stage
            can_create = True
            skip_reason = None

            if existing_stages:
                # Check if any stage is still active (scheduled or active)
                active_stages = [s for s in existing_stages if s.status in {"scheduled", "active"}]
                if active_stages:
                    can_create = False
                    skip_reason = f"already has active stage (status: {active_stages[0].status})"
                elif not stage_def.multiple_callable:
                    can_create = False
                    skip_reason = "not marked as multiple_callable in stage definition"

            if not can_create:
                continue

            # Check requirements
            requirements_met = stage_def.check_requirements(doc)
            stages_evaluated += 1

            if requirements_met:
                # Create stage in active status (requirements are met)
                new_stage = doc.add_stage(stage_name, status="active")
                stages_started += 1
                started_stages.append({
                    "name": stage_name,
                    "id": new_stage.id,
                    "counter": new_stage.counter
                })

                # Trigger workflows for this stage
                try:
                    triggered_workflows = stage_def.trigger_workflows(doc, new_stage.counter)
                    if triggered_workflows:
                        started_stages[-1]["workflows_triggered"] = len(triggered_workflows)
                    else:
                        started_stages[-1]["workflows_triggered"] = 0
                except Exception as e:
                    started_stages[-1]["workflow_error"] = str(e)

        # Update document status to "active" if it was "inbox" and has stages
        if doc.status == "inbox" and len(doc.stages) > 0:
            doc.status = "active"

        # Save document after all stage evaluations
        doc.save()

        return {
            "success": True,
            "message": f"Stage evaluation completed for document {docId}",
            "docId": docId,
            "triggered_by": triggered_by,
            "stages_evaluated": stages_evaluated,
            "stages_started": stages_started,
            "started_stages": started_stages,
            "document_status": doc.status
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Stage evaluation failed: {str(e)}",
            "docId": docId,
            "triggered_by": triggered_by
        }

