from __future__ import annotations
import typer
from typing import Optional, List
from idflow.core.fs_markdown import FSMarkdownDocument
from idflow.core.stage_definitions import get_stage_definitions


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

    # Get stage definitions
    stage_definitions = get_stage_definitions()
    available_stages = stage_definitions.list_definitions()

    if not available_stages:
        typer.echo("No stage definitions found", err=True)
        raise typer.Exit(1)

    # Filter stages if specific stage requested
    stages_to_evaluate = available_stages
    if stage:
        if stage not in available_stages:
            typer.echo(f"Stage '{stage}' not found", err=True)
            typer.echo(f"Available stages: {', '.join(available_stages)}", err=True)
            raise typer.Exit(1)
        stages_to_evaluate = [stage]

    # Get documents to evaluate
    if uuid:
        # Single document
        doc = FSMarkdownDocument.find(uuid)
        if not doc:
            typer.echo(f"Document with UUID {uuid} not found", err=True)
            raise typer.Exit(1)
        documents = [doc]
    else:
        # All documents with specified status
        documents = FSMarkdownDocument.where(status=status)

    if not documents:
        typer.echo(f"No documents found with status '{status}'", err=True)
        raise typer.Exit(1)

    # Track results
    total_evaluated = 0
    stages_started = 0
    stages_skipped = 0

    typer.echo(f"Evaluating {len(documents)} documents against {len(stages_to_evaluate)} stages...")

    for doc in documents:
        typer.echo(f"\nDocument {doc.id} (status: {doc.status}):")

        # Track if document has any stages (existing or newly created)
        has_stages = len(doc.stages) > 0

        for stage_name in stages_to_evaluate:
            stage_def = stage_definitions.get_definition(stage_name)
            if not stage_def:
                continue

            # Check if stage already exists for this document
            existing_stages = doc.get_stages(stage_name)

            # Determine if we can create/rerun this stage
            can_create = True
            skip_reason = None

            if existing_stages:
                # Check if any stage is still active (scheduled or active)
                active_stages = [s for s in existing_stages if s.status in {"scheduled", "active"}]
                if active_stages:
                    can_create = False
                    skip_reason = f"already has active stage (status: {active_stages[0].status})"
                elif not allow_rerun:
                    can_create = False
                    skip_reason = "already exists (use --allow-rerun to rerun completed stages)"
                elif not stage_def.multiple_callable:
                    can_create = False
                    skip_reason = "not marked as multiple_callable in stage definition"

            if not can_create:
                typer.echo(f"  {stage_name}: SKIPPED - {skip_reason}")
                stages_skipped += 1
                continue

            # Check requirements
            requirements_met = stage_def.check_requirements(doc)
            total_evaluated += 1

            if requirements_met:
                # Create stage in active status (requirements are met)
                new_stage = doc.add_stage(stage_name, status="active")
                has_stages = True  # Mark that document now has stages

                # Trigger workflows for this stage
                try:
                    triggered_workflows = stage_def.trigger_workflows(doc)
                    if triggered_workflows:
                        typer.echo(f"  {stage_name}: STARTED - requirements met (stage ID: {new_stage.id}) - {len(triggered_workflows)} workflows triggered")
                    else:
                        typer.echo(f"  {stage_name}: STARTED - requirements met (stage ID: {new_stage.id}) - no workflows triggered")
                except Exception as e:
                    typer.echo(f"  {stage_name}: STARTED - requirements met (stage ID: {new_stage.id}) - workflow trigger failed: {e}")

                stages_started += 1
            else:
                typer.echo(f"  {stage_name}: SKIPPED - requirements not met")
                stages_skipped += 1

        # Update document status to "active" if it was "inbox" and has stages
        if doc.status == "inbox" and has_stages:
            doc.status = "active"
            typer.echo(f"  Document status changed: inbox → active (has {len(doc.stages)} stage(s))")

        # Save document after all stage evaluations
        doc.save()

    # Summary
    typer.echo(f"\nSummary:")
    typer.echo(f"  Documents evaluated: {len(documents)}")
    typer.echo(f"  Stage evaluations: {total_evaluated}")
    typer.echo(f"  Stages started: {stages_started}")
    typer.echo(f"  Stages skipped: {stages_skipped}")
