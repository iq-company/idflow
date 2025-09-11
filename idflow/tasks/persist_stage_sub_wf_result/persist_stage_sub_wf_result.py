# TYPE: PERSIST_STAGE_SUB_WF_RESULT

from conductor.client.worker.worker_task import worker_task
from typing import Any
from idflow.core.document_factory import get_document_class


@worker_task(task_definition_name='persist_stage_sub_wf_result')
def persist_stage_sub_wf_result(
    workflow_results: dict[str, Any],
    doc_id: str,
    stage_name: str,
    stage_counter: int,
    sub_workflow_name: str
) -> dict[str, Any]:
    """
    Persistiert die Ergebnisse eines Sub-Workflows als Markdown-Datei mit Frontmatter.

    Args:
        workflow_results: Die Ergebnisse des Sub-Workflows
        doc_id: Document ID für das Verzeichnis
        stage_name: Name der Stage
        stage_counter: Stage Counter für das Verzeichnis
        sub_workflow_name: Name des Sub-Workflows für den Dateinamen

    Returns:
        Dictionary mit dem Status der Speicherung
    """
    try:
        # Prüfe ob doc-Attribut in den Workflow-Ergebnissen vorhanden ist
        if 'doc' not in workflow_results:
            return {
                "success": True,
                "message": "No doc attribute found in workflow results, nothing to persist",
                "sub_workflow_name": sub_workflow_name,
                "doc_id": doc_id
            }

        doc_content = workflow_results['doc']

        # Normalisiere doc_content zu einem Dictionary
        if isinstance(doc_content, str):
            # Wenn es ein String ist, erstelle ein Dict mit dem String als 'body'
            doc_dict = {"body": doc_content}
        elif isinstance(doc_content, dict):
            doc_dict = doc_content.copy()
        else:
            # Fallback: konvertiere zu String und erstelle Dict
            doc_dict = {"body": str(doc_content)}

        # Lade das Document über die ORM find API
        DocumentClass = get_document_class()
        doc = DocumentClass.find(doc_id)
        if not doc:
            return {
                "success": False,
                "error": f"Document with ID {doc_id} not found",
                "sub_workflow_name": sub_workflow_name,
                "doc_id": doc_id,
                "stage_name": stage_name,
                "stage_counter": stage_counter
            }

        # Hole die Stage-Instanz
        stage = doc.get_stage(stage_name, stage_counter)
        if not stage:
            return {
                "success": False,
                "error": f"Stage {stage_name} with counter {stage_counter} not found",
                "sub_workflow_name": sub_workflow_name,
                "doc_id": doc_id,
                "stage_name": stage_name,
                "stage_counter": stage_counter
            }

        # Nutze die Stage-API für das Persistieren
        file_path = stage.persist_sub_doc_frontmatter(sub_workflow_name, doc_dict)

        return {
            "success": True,
            "message": f"Successfully persisted sub-workflow result to {file_path}",
            "sub_workflow_name": sub_workflow_name,
            "doc_id": doc_id,
            "stage_name": stage_name,
            "stage_counter": stage_counter,
            "sub_doc_name": file_path.name
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to persist sub-workflow result: {str(e)}",
            "sub_workflow_name": sub_workflow_name,
            "doc_id": doc_id,
            "stage_name": stage_name,
            "stage_counter": stage_counter
        }
