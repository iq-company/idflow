from __future__ import annotations
import typer
from typing import Optional, List
from idflow.core.document_factory import get_document_class


def evaluate(
    status: str = typer.Option("inbox", "--status", help="Document status to filter by"),
    stage: Optional[str] = typer.Option(None, "--stage", help="Specific stage name to evaluate"),
    uuid: Optional[str] = typer.Option(None, "--uuid", help="Specific document UUID to evaluate"),
    allow_rerun: bool = typer.Option(False, "--allow-rerun", help="Allow rerunning completed stages with multiple_callable: true"),
):
    """
    Evaluate stage requirements for documents and automatically start stages where requirements are met.

    Without parameters: Evaluates all documents in inbox status against all configured stages.
    With filters: Only evaluates specific documents and/or stages.
    """
    # Get document class from factory
    DocumentClass = get_document_class()

    # Get documents to evaluate
    if uuid:
        # Single document
        doc = DocumentClass.find(uuid)
        if not doc:
            typer.echo(f"Document with UUID {uuid} not found", err=True)
            raise typer.Exit(1)
        documents = [doc]
    else:
        # All documents with specified status
        documents = DocumentClass.where(status=status)

    if not documents:
        typer.echo(f"No documents found with status '{status}'", err=True)
        raise typer.Exit(1)

    # Track overall results
    total_documents = len(documents)
    total_evaluated = 0
    total_started = 0
    total_skipped = 0

    typer.echo(f"Evaluating {total_documents} documents...")

    for doc in documents:
        typer.echo(f"\nDocument {doc.id} (status: {doc.status}):")

        # Use document's evaluate_stages method
        result = doc.evaluate_stages(stage_name=stage, allow_rerun=allow_rerun)

        if not result["success"]:
            typer.echo(f"  ERROR: {result.get('error', 'Unknown error')}", err=True)
            continue

        # Display results for this document
        for started_stage in result["started_stages"]:
            workflows_info = f" - {started_stage['workflows_triggered']} workflows triggered" if started_stage['workflows_triggered'] > 0 else " - no workflows triggered"
            typer.echo(f"  {started_stage['name']}: STARTED - requirements met (stage ID: {started_stage['id']}){workflows_info}")

        for skipped_stage in result["skipped_stages"]:
            typer.echo(f"  {skipped_stage['name']}: SKIPPED - {skipped_stage['reason']}")

        # Show status change if it occurred
        if result["status_changed"]:
            typer.echo(f"  Document status changed: inbox → active (has {len(doc.stages)} stage(s))")

        # Update totals
        total_evaluated += result["stages_evaluated"]
        total_started += result["stages_started"]
        total_skipped += result["stages_skipped"]

        # Save document after evaluation
        doc.save()

    # Summary
    typer.echo(f"\nSummary:")
    typer.echo(f"  Documents evaluated: {total_documents}")
    typer.echo(f"  Stage evaluations: {total_evaluated}")
    typer.echo(f"  Stages started: {total_started}")
    typer.echo(f"  Stages skipped: {total_skipped}")
