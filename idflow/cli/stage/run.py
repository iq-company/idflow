from __future__ import annotations
import typer
from typing import Optional
from idflow.core.fs_markdown import FSMarkdownDocument
from idflow.core.stage_definitions import get_stage_definitions


def run(
    stage_name: str = typer.Argument(..., help="Name of the stage to run"),
    doc_uuid: str = typer.Argument(..., help="UUID of the document"),
    workflow_name: Optional[str] = typer.Argument(None, help="Optional specific workflow to run"),
):
    """Manually start a stage for a document."""

    # Load the document
    doc = FSMarkdownDocument.find(doc_uuid)
    if not doc:
        typer.echo(f"Document with UUID {doc_uuid} not found", err=True)
        raise typer.Exit(1)

    # Check if stage definition exists
    stage_definitions = get_stage_definitions()
    stage_definition = stage_definitions.get_definition(stage_name)
    if not stage_definition:
        typer.echo(f"Stage definition '{stage_name}' not found", err=True)
        typer.echo(f"Available stages: {', '.join(stage_definitions.list_definitions())}", err=True)
        raise typer.Exit(1)

    # Check if workflow is specified and exists in stage definition
    if workflow_name:
        workflow_found = any(wf.name == workflow_name for wf in stage_definition.workflows)
        if not workflow_found:
            typer.echo(f"Workflow '{workflow_name}' not found in stage '{stage_name}'", err=True)
            available_workflows = [wf.name for wf in stage_definition.workflows]
            typer.echo(f"Available workflows: {', '.join(available_workflows)}", err=True)
            raise typer.Exit(1)

    # Add the stage to the document
    stage = doc.add_stage(stage_name)

    # Save the document (this will trigger the stage's before_save logic)
    doc.save()

    # Output the stage ID
    typer.echo(stage.id)
