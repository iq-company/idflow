from __future__ import annotations
import typer
from typing import Optional
from idflow.core.workflow_manager import get_workflow_manager
from idflow.core.discovery import required_workflow_names_static


def upload_workflows(
    force: bool = typer.Option(False, "--force", help="Force upload even if up to date"),
    workflow: Optional[str] = typer.Option(None, "--workflow", "-w", help="Specific workflow name to upload")
):
    """Upload all workflows to Conductor. Tasks are automatically registered via @worker_task decorators."""
    workflow_manager = get_workflow_manager()

    if workflow:
        typer.echo(f"Uploading workflow '{workflow}' to Conductor...")
        typer.echo("Note: Tasks are automatically registered via @worker_task decorators when workers start.")

        results = workflow_manager.upload_single_workflow(workflow, force=force)
    else:
        typer.echo("Uploading workflows (active only)...")
        typer.echo("Note: Tasks are automatically registered via @worker_task decorators when workers start.")

        # Determine required workflows from active stages
        required = set(required_workflow_names_static())
        if not required:
            typer.echo("No active workflows required by stages. Use --workflow to upload specific workflow.")
            return

        # Upload required workflows
        results = {}
        for name in sorted(required):
            single = workflow_manager.upload_single_workflow(name, force=force)
            results.update(single)

    # Show results only for actually uploaded workflows
    if hasattr(workflow_manager, '_last_upload_results'):
        upload_results = workflow_manager._last_upload_results

        if upload_results['uploaded']:
            typer.echo("\nWorkflow upload results:")
            for name in upload_results['uploaded']:
                typer.echo(f"  ✓ {name}")

        if upload_results['skipped']:
            typer.echo(f"\nSkipped {len(upload_results['skipped'])} workflows (already up to date)")

        # Summary
        uploaded_count = len(upload_results['uploaded'])
        total_count = upload_results['total']

        if uploaded_count > 0:
            typer.echo(f"\nSummary: {uploaded_count}/{total_count} workflows uploaded successfully")
        else:
            typer.echo(f"\nSummary: All {total_count} workflows are up to date")
    else:
        # Fallback for old behavior
        typer.echo("\nWorkflow upload results:")
        for name, success in results.items():
            status = "✓" if success else "✗"
            typer.echo(f"  {status} {name}")

    typer.echo("Tasks will be automatically registered when workers start.")
